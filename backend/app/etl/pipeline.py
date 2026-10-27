"""Motor de carga: o mesmo para todas as fontes.

Por unidade de origem (um arquivo, um cliente Metryx, uma fazenda do histórico):
  1. registra a unidade; assinatura igual à da última carga -> 'inalterada' (nem lê o conteúdo);
  2. extrai o bruto; sha256 igual ao da última versão carregada -> 'inalterada';
  3. cópia com os mesmos bytes de um arquivo mais recente -> 'ignorada' (duplicatas.py);
  4. grava a versão (e o bruto JSON em raw.payload) — permite reprocessar sem reler a fonte;
  5. normaliza (adapter: bruto -> LoteCanonico);
  6. numa ÚNICA transação (`carregar_lote`): valida o contrato, trava as fazendas, resolve identidades, confere arquivo
     em dobro, checa qualidade, aplica as partições, recalcula o estoque e grava o diagnóstico.
Erro numa unidade não afeta as outras nem apaga dados: a versão anterior continua valendo.
"""

import logging
import traceback
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, func, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.session import sessao
from app.etl import diagnostico, duplicatas, loaders, quality
from app.etl.adapters.base import Bruto, SourceAdapter, UnidadeOrigem
from app.etl.canonical import LinhaRejeitada, LoteCanonico, Ocorrencia, Particao
from app.etl.diagnostico import Diagnostico
from app.etl.duplicatas import ErroUnidadeDuplicada
from app.etl.mapping import Resolvido, dominio, resolver
from app.etl.quality import Cod
from app.models.ingest import Job, Payload, VersaoOrigem
from app.models.ingest import Ocorrencia as OcorrenciaDb
from app.models.ingest import UnidadeOrigem as UnidadeOrigemDb

log = logging.getLogger(__name__)


class ErroContrato(Exception):
    def __init__(self, erros: list[str]):
        super().__init__(f"{len(erros)} violação(ões) de contrato: " + "; ".join(erros[:5]))
        self.erros = erros


@dataclass
class ResultadoUnidade:
    chave: str
    status: str                              # carregada | carregada_com_avisos | inalterada | ignorada | erro
    versao_id: UUID | None = None
    gravadas: Counter = field(default_factory=Counter)
    apagadas: Counter = field(default_factory=Counter)
    quarentena: int = 0
    avisos: int = 0
    erro: str | None = None


@dataclass
class ResultadoJob:
    job_id: UUID
    status: str
    unidades: list[ResultadoUnidade]


@dataclass
class UnidadeRegistrada:
    """O que o banco sabe da unidade antes de processá-la."""
    id: UUID
    assinatura: str | None
    ultima_versao_id: UUID | None
    sha256_da_ultima_versao: str | None


class MotorCarga:
    def __init__(self, engine: Engine, hoje: date | None = None, estoque_ate: date | None = None,
                 ignorar_guarda: bool = False):
        self.engine = engine
        self.hoje = hoje
        self.estoque_ate = estoque_ate
        self.ignorar_guarda = ignorar_guarda   # True só por decisão explícita (queda legítima de volume na fonte)

    def data_do_estoque(self) -> date:
        """Até quando o estoque mensal é recalculado (meses sem evento repetem o saldo)."""
        return self.estoque_ate or self.hoje or date.today()

    # --- orquestração ----------------------------------------------------------------------------------------------

    def executar(self, adapter: SourceAdapter, unidades: list[UnidadeOrigem] | None = None, *, forcar: bool = False,
                 usuario_id: UUID | None = None) -> ResultadoJob:
        job_id = self._abrir_job(adapter.fonte, forcar, usuario_id)
        if unidades is None:
            unidades = adapter.descobrir()
        resultados = []
        for unidade in unidades:
            resultados.append(self.processar_unidade(adapter, unidade, job_id=job_id, forcar=forcar))
        status = status_do_job(resultados)
        self._fechar_job(job_id, status, resultados)
        return ResultadoJob(job_id, status, resultados)

    def processar_unidade(self, adapter: SourceAdapter, unidade: UnidadeOrigem, *, job_id: UUID | None = None,
                          forcar: bool = False) -> ResultadoUnidade:
        registrada = self._registrar_unidade(adapter.fonte, unidade)
        assinatura_igual = unidade.assinatura and registrada.assinatura == unidade.assinatura
        if not forcar and assinatura_igual and registrada.ultima_versao_id is not None:
            return ResultadoUnidade(unidade.chave, "inalterada", registrada.ultima_versao_id)

        try:
            bruto = adapter.extrair(unidade)
        except Exception as exc:  # noqa: BLE001 — erro de uma unidade nunca derruba o job
            log.exception("falha ao extrair %s", unidade.chave)
            self._registrar_erro(job_id, None, Cod.EXTRACT_FAILED, exc)
            return ResultadoUnidade(unidade.chave, "erro", erro=str(exc))

        if not forcar and registrada.sha256_da_ultima_versao == bruto.sha256:
            self._guardar_assinatura(registrada.id, unidade.assinatura)
            return ResultadoUnidade(unidade.chave, "inalterada", registrada.ultima_versao_id)

        copia = duplicatas.copia_identica(self.engine, adapter.fonte, registrada.id, bruto.sha256)
        if copia and copia.mais_recente:
            duplicatas.ignorar_copia(self.engine, job_id, registrada.id, unidade.chave, copia.chave, bruto.sha256)
            return ResultadoUnidade(unidade.chave, "ignorada", erro=f"conteúdo idêntico a {copia.chave}, mais recente")

        try:
            versao_id = self._registrar_versao(adapter.fonte, registrada.id, bruto, job_id)
        except Exception as exc:  # noqa: BLE001 — bruto que não grava (ex.: não JSON-ável) derruba só a unidade
            log.exception("falha ao registrar a versão de %s", unidade.chave)
            self._registrar_erro(job_id, None, Cod.EXTRACT_FAILED, exc)
            return ResultadoUnidade(unidade.chave, "erro", erro=str(exc))

        resultado = self._normalizar_e_carregar(adapter, bruto, registrada.id, versao_id, job_id, unidade.assinatura)
        if copia and resultado.status.startswith("carregada"):      # a cópia antiga, idêntica, sai com o que gravou
            duplicatas.aposentar_copia(self.engine, job_id, copia, unidade.chave, bruto.sha256, self.data_do_estoque())
        return resultado

    def reprocessar(self, adapter: SourceAdapter, versao_id: UUID, *, job_id: UUID | None = None) -> ResultadoUnidade:
        """Renormaliza uma versão a partir do bruto guardado (JSON) ou relendo a unidade (arquivo)."""
        with sessao(self.engine) as s:
            versao = s.get(VersaoOrigem, versao_id)
            registro = s.get(UnidadeOrigemDb, versao.unidade_id)
            unidade = UnidadeOrigem(chave=registro.chave, descricao=registro.descricao or registro.chave,
                                    metadados=registro.metadados or {})
            conteudo = s.scalar(select(Payload.conteudo).where(Payload.versao_origem_id == versao_id)
                                .order_by(Payload.recebido_em.desc()).limit(1))
        if conteudo is not None:
            bruto = Bruto(unidade, "json", conteudo, versao.sha256, versao.tamanho_bytes or 0, versao.metadados or {})
        else:
            bruto = adapter.extrair(unidade)
            if bruto.sha256 != versao.sha256:
                raise ValueError(f"o conteúdo de {registro.chave} mudou desde a versão {versao_id}; "
                                 "faça uma carga nova")
        return self._normalizar_e_carregar(adapter, bruto, registro.id, versao_id, job_id, None)

    # --- etapas fora da transação de carga ---------------------------------------------------------------------------

    def _abrir_job(self, fonte: str, forcar: bool, usuario_id: UUID | None) -> UUID:
        with sessao(self.engine) as s:
            return s.scalar(pg_insert(Job).values(
                fonte=fonte, tipo="carga", status="processando", usuario_id=usuario_id, parametros={"forcar": forcar},
                iniciado_em=func.now()).returning(Job.id))

    def _fechar_job(self, job_id: UUID, status: str, resultados: list[ResultadoUnidade]) -> None:
        contagem = Counter(resultado.status for resultado in resultados)
        detalhe = []
        for resultado in resultados:
            detalhe.append({"chave": resultado.chave, "status": resultado.status, "erro": resultado.erro,
                            "gravadas": dict(resultado.gravadas), "quarentena": resultado.quarentena})
        with sessao(self.engine) as s:
            s.execute(update(Job).where(Job.id == job_id).values(
                status=status, finalizado_em=func.now(), unidades_total=len(resultados),
                unidades_carregadas=contagem["carregada"] + contagem["carregada_com_avisos"],
                unidades_inalteradas=contagem["inalterada"], unidades_com_erro=contagem["erro"],
                detalhe={"unidades": detalhe}))

    def _registrar_unidade(self, fonte: str, unidade: UnidadeOrigem) -> UnidadeRegistrada:
        """Cria a unidade ou atualiza a que já existe (volta a ficar 'ativa' a cada vez que é vista)."""
        with sessao(self.engine) as s:
            comando = pg_insert(UnidadeOrigemDb).values(fonte=fonte, chave=unidade.chave,
                                                        descricao=unidade.descricao, metadados=unidade.metadados)
            unidade_id = s.scalar(comando.on_conflict_do_update(
                constraint="uq_unidade_origem",
                set_={"descricao": comando.excluded.descricao, "metadados": comando.excluded.metadados,
                      "ultimo_visto_em": func.now(), "status": "ativa"},
            ).returning(UnidadeOrigemDb.id))
            registro = s.get(UnidadeOrigemDb, unidade_id)
            sha256 = s.scalar(select(VersaoOrigem.sha256).where(VersaoOrigem.id == registro.ultima_versao_id))
            return UnidadeRegistrada(unidade_id, registro.assinatura, registro.ultima_versao_id, sha256)

    def _guardar_assinatura(self, unidade_id: UUID, assinatura: str | None) -> None:
        with sessao(self.engine) as s:
            s.execute(update(UnidadeOrigemDb).where(UnidadeOrigemDb.id == unidade_id).values(assinatura=assinatura))

    def _registrar_versao(self, fonte: str, unidade_id: UUID, bruto: Bruto, job_id: UUID | None) -> UUID:
        with sessao(self.engine) as s:
            comando = pg_insert(VersaoOrigem).values(unidade_id=unidade_id, sha256=bruto.sha256,
                                                     tamanho_bytes=bruto.tamanho_bytes, metadados=bruto.metadados,
                                                     job_id=job_id, status="extraida")
            versao_id = s.scalar(comando.on_conflict_do_update(
                constraint="uq_versao_origem", set_={"job_id": comando.excluded.job_id, "status": "extraida"}
            ).returning(VersaoOrigem.id))
            if bruto.formato == "json":
                itens = len(bruto.conteudo) if isinstance(bruto.conteudo, list) else None
                s.execute(pg_insert(Payload).values(
                    versao_origem_id=versao_id, fonte=fonte, endpoint=bruto.metadados.get("endpoint"),
                    http_status=bruto.metadados.get("http_status"), qtd_itens=itens, conteudo=bruto.conteudo))
        return versao_id

    def _normalizar_e_carregar(self, adapter: SourceAdapter, bruto: Bruto, unidade_id: UUID, versao_id: UUID,
                               job_id: UUID | None, assinatura: str | None) -> ResultadoUnidade:
        chave = bruto.unidade.chave
        try:
            lote = adapter.normalizar(bruto)
        except Exception as exc:  # noqa: BLE001
            log.exception("falha ao normalizar %s", chave)
            self._registrar_erro(job_id, versao_id, Cod.NORMALIZE_FAILED, exc)
            return ResultadoUnidade(chave, "erro", versao_id, erro=str(exc))

        try:
            with sessao(self.engine) as s:
                resultado = self.carregar_lote(s, lote, versao_id=versao_id, unidade_id=unidade_id, job_id=job_id)
                resultado.chave = chave
                s.execute(update(UnidadeOrigemDb).where(UnidadeOrigemDb.id == unidade_id)
                          .values(ultima_versao_id=versao_id, assinatura=assinatura))
            return resultado
        except ErroContrato as exc:
            self._registrar_erro(job_id, versao_id, Cod.CONTRACT_VIOLATION, exc, {"erros": exc.erros[:100]})
            return ResultadoUnidade(chave, "erro", versao_id, erro=str(exc))
        except ErroUnidadeDuplicada as exc:
            # a versão fica 'extraida' (lida, não carregada) e a unidade 'ignorada'; volta a ser lida a cada carga,
            # então assume a fazenda se o arquivo mais recente sumir
            self._registrar_erro(job_id, versao_id, Cod.DUPLICATE_UNIT_FILE, exc, nivel="aviso")
            with sessao(self.engine) as s:
                s.execute(update(UnidadeOrigemDb).where(UnidadeOrigemDb.id == unidade_id).values(status="ignorada"))
            return ResultadoUnidade(chave, "ignorada", versao_id, erro=str(exc))
        except Exception as exc:  # noqa: BLE001
            log.exception("falha ao carregar %s", chave)
            self._registrar_erro(job_id, versao_id, Cod.LOAD_FAILED, exc)
            return ResultadoUnidade(chave, "erro", versao_id, erro=str(exc))

    def _registrar_erro(self, job_id: UUID | None, versao_id: UUID | None, codigo: Cod, exc: Exception,
                        contexto: dict[str, Any] | None = None, nivel: str = "erro") -> None:
        with sessao(self.engine) as s:
            if versao_id is not None and nivel == "erro":
                s.execute(update(VersaoOrigem).where(VersaoOrigem.id == versao_id).values(status="erro"))
            s.execute(pg_insert(OcorrenciaDb).values(
                job_id=job_id, versao_origem_id=versao_id, nivel=nivel, codigo=codigo, mensagem=str(exc)[:2000],
                contexto=contexto or {"traceback": traceback.format_exception(exc)[-3:]}))

    # --- carga de um lote (uma transação) ----------------------------------------------------------------------------

    def carregar_lote(self, s: Session, lote: LoteCanonico, *, versao_id: UUID, unidade_id: UUID | None = None,
                      job_id: UUID | None = None) -> ResultadoUnidade:
        erros = lote.validar_contrato()
        if erros:
            raise ErroContrato(erros)
        travar_fazendas(s, lote)
        resolvido = resolver(s, lote)
        if unidade_id is not None:
            duplicatas.conferir_arquivo_em_dobro(s, lote, list(resolvido.fazendas.values()), unidade_id)

        avisos = Diagnostico(ocorrencias=[*lote.ocorrencias, *resolvido.ocorrencias], rejeitadas=list(lote.rejeitadas))
        linhas_por_particao = self._linhas_por_particao(lote, resolvido, versao_id, job_id, avisos)
        resultado = ResultadoUnidade(chave="", status="carregada", versao_id=versao_id)
        fazendas_do_estoque = self._aplicar_particoes(s, lote, resolvido, linhas_por_particao, resultado, avisos)
        if fazendas_do_estoque:
            s.execute(text("SELECT fato.recalcular_estoque_mensal(CAST(:f AS uuid[]), CAST(:ate AS date))"),
                      {"f": list(fazendas_do_estoque), "ate": self.data_do_estoque()})

        avisos.ocorrencias.extend(diagnostico.pendencias_de_categoria(s, resolvido))
        avisos.ocorrencias.extend(diagnostico.pendencias_de_conta(s, resolvido, lote))
        diagnostico.gravar(s, avisos, resolvido, versao_id, unidade_id, job_id)
        resultado.quarentena = len(avisos.rejeitadas)
        resultado.avisos = avisos.avisos()
        resultado.status = "carregada_com_avisos" if resultado.quarentena or resultado.avisos else "carregada"
        fechar_versao(s, lote, resultado.status, versao_id, unidade_id)
        return resultado

    def _linhas_por_particao(self, lote: LoteCanonico, resolvido: Resolvido, versao_id: UUID, job_id: UUID | None,
                             avisos: Diagnostico) -> list[list[dict[str, Any]]]:
        """Checa a qualidade de cada linha e a converte para o banco, agrupada pela partição que a cobre."""
        linhas_por_particao: list[list[dict[str, Any]]] = [[] for _ in lote.particoes]
        for entidade in loaders.TABELAS:
            for linha in lote.linhas(entidade):
                checagem = quality.checar(entidade, linha, self.hoje)
                avisos.ocorrencias.extend(checagem.ocorrencias)
                if checagem.rejeitar:
                    avisos.rejeitadas.append(linha_rejeitada(entidade, linha, checagem.codigo, checagem.motivo))
                    continue
                registro = linha_para_banco(linha, resolvido)
                registro.update(fonte=lote.fonte, origem_ref=versao_id, origem_linha=linha.origem_linha,
                                extra=linha.extra, ingest_job_id=job_id)
                linhas_por_particao[indice_da_particao(lote.particoes, entidade, linha)].append(registro)
        return linhas_por_particao

    def _aplicar_particoes(self, s: Session, lote: LoteCanonico, resolvido: Resolvido,
                           linhas_por_particao: list[list[dict]], resultado: ResultadoUnidade,
                           avisos: Diagnostico) -> set[UUID]:
        """Grava cada partição; devolve as fazendas cujo estoque precisa ser recalculado."""
        fazendas_do_estoque: set[UUID] = set()
        for particao, linhas in zip(lote.particoes, linhas_por_particao, strict=True):
            fazenda_id = resolvido.fazendas[particao.fazenda]
            if not self._fonte_ativa(lote, resolvido, particao, fazenda_id, len(linhas), avisos):
                continue
            versao_plano_id = None
            if particao.versao_plano:
                versao_plano_id = resolvido.versoes[(resolvido.cliente_da_fazenda[particao.fazenda],
                                                     particao.versao_plano)]
            no_banco = loaders.ParticaoDb(particao.entidade, lote.fonte, fazenda_id, particao.cenario,
                                          particao.estrategia, particao.tipos, versao_plano_id,
                                          particao.guarda_volume, particao.desde, particao.ate)
            aplicada = loaders.aplicar(s, no_banco, linhas, ignorar_guarda=self.ignorar_guarda)
            if aplicada.retida:
                avisos.ocorrencias.append(aviso_de_guarda(particao, len(linhas), aplicada.existentes))
                continue
            resultado.apagadas[particao.entidade] += aplicada.apagadas
            resultado.gravadas[particao.entidade] += aplicada.gravadas
            if particao.entidade in ("mov_animal", "inventario") and particao.cenario == "realizado":
                fazendas_do_estoque.add(fazenda_id)
        return fazendas_do_estoque

    @staticmethod
    def _fonte_ativa(lote: LoteCanonico, resolvido: Resolvido, particao: Particao, fazenda_id: UUID,
                     quantidade: int, avisos: Diagnostico) -> bool:
        """Cada domínio da fazenda tem uma fonte ativa (planilha ou Metryx); dado de outra fonte não entra."""
        dominio_da_particao = dominio(particao.entidade, particao.cenario)
        ativa = resolvido.fonte_ativa.get((fazenda_id, dominio_da_particao))
        if ativa == lote.fonte:
            return True
        avisos.ocorrencias.append(Ocorrencia(
            nivel="aviso", codigo=Cod.SOURCE_INACTIVE_FOR_DOMAIN, fazenda=particao.fazenda, entidade=particao.entidade,
            mensagem=f"{lote.fonte} não é a fonte ativa de '{dominio_da_particao}' (ativa: {ativa}); "
                     f"{quantidade} linha(s) ignorada(s)"))
        return False


# --- funções de apoio ----------------------------------------------------------------------------------------------

def status_do_job(resultados: list[ResultadoUnidade]) -> str:
    contagem = Counter(resultado.status for resultado in resultados)
    if contagem["erro"] and contagem["erro"] == len(resultados):
        return "erro"
    if contagem["erro"] or contagem["carregada_com_avisos"]:
        return "concluido_com_avisos"
    return "concluido"


def travar_fazendas(s: Session, lote: LoteCanonico) -> None:
    """Serializa cargas concorrentes das mesmas fazendas (sempre na mesma ordem, para não haver deadlock)."""
    for fazenda in sorted({fazenda.id_externo for fazenda in lote.fazendas}):
        s.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"carga:{lote.fonte}:{fazenda}"})


def indice_da_particao(particoes: list[Particao], entidade: str, linha: Any) -> int:
    """Posição da partição que cobre a linha (o contrato já garantiu que existe exatamente uma)."""
    for indice, particao in enumerate(particoes):
        if particao.cobre(entidade, linha):
            return indice
    raise ValueError(f"{entidade} {linha.origem_linha}: nenhuma partição cobre a linha")


def aviso_de_guarda(particao: Particao, novas: int, existentes: int) -> Ocorrencia:
    tipos = " " + ",".join(particao.tipos) if particao.tipos else ""
    return Ocorrencia(
        nivel="aviso", codigo=Cod.SNAPSHOT_HELD, fazenda=particao.fazenda, entidade=particao.entidade,
        mensagem=f"{particao.entidade}{tipos}: a fonte trouxe {novas} linha(s) e havia {existentes}; dados mantidos "
                 "até confirmação",
        contexto={"existentes": existentes, "novas": novas})


def fechar_versao(s: Session, lote: LoteCanonico, status: str, versao_id: UUID, unidade_id: UUID | None) -> None:
    """Marca a versão como carregada (com a impressão dos dados, usada no aviso de arquivo em dobro) e as versões
    anteriores da unidade como substituídas."""
    metadados = s.scalar(select(VersaoOrigem.metadados).where(VersaoOrigem.id == versao_id)) or {}
    metadados = {**metadados, "impressao_dados": lote.impressao_dados(), "linhas_dados": lote.linhas_dados()}
    s.execute(update(VersaoOrigem).where(VersaoOrigem.id == versao_id)
              .values(status=status, carregado_em=func.now(), metadados=metadados))
    if unidade_id is not None:
        s.execute(update(VersaoOrigem)
                  .where(VersaoOrigem.unidade_id == unidade_id, VersaoOrigem.id != versao_id,
                         VersaoOrigem.status.in_(("carregada", "carregada_com_avisos")))
                  .values(status="substituida"))


def linha_rejeitada(entidade: str, linha: Any, codigo: str, motivo: str) -> LinhaRejeitada:
    return LinhaRejeitada(entidade=entidade, origem_linha=linha.origem_linha, codigo=codigo, motivo=motivo,
                          dados=linha.model_dump(mode="json"), fazenda=getattr(linha, "fazenda", None))


def linha_para_banco(linha: Any, resolvido: Resolvido) -> dict[str, Any]:
    """Linha canônica -> colunas do banco, trocando as identidades externas pelos ids internos."""
    colunas = linha.model_dump(exclude={"origem_linha", "extra"})
    registro: dict[str, Any] = {"fazenda_id": resolvido.fazendas[colunas.pop("fazenda")]}
    if "retiro" in colunas:
        retiro = colunas.pop("retiro")
        registro["retiro_id"] = resolvido.retiros[retiro] if retiro else None
    if "versao_plano" in colunas:
        versao = colunas.pop("versao_plano")
        cliente = resolvido.cliente_da_fazenda[linha.fazenda]
        registro["versao_plano_id"] = resolvido.versoes[(cliente, versao)] if versao else None
    if "categoria" in colunas:
        colunas.pop("categoria")
        registro["categoria_map_id"] = resolvido.categorias[linha.categoria] if linha.categoria is not None else None
    if "categoria_destino" in colunas:
        colunas.pop("categoria_destino")
        destino = linha.categoria_destino
        registro["categoria_destino_map_id"] = resolvido.categorias[destino] if destino is not None else None
    if "conta" in colunas:
        colunas.pop("conta")
        registro["plano_contas_map_id"] = resolvido.contas[linha.conta]
    if "fazenda_fiscal" in colunas:
        fiscal = colunas.pop("fazenda_fiscal")
        registro["fazenda_fiscal_id"] = resolvido.fazendas.get(fiscal) if fiscal else None
    registro.update(colunas)
    return registro

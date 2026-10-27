#!/bin/sh
# Traz as planilhas do Google Drive para a VPS: rclone, só leitura no Drive, a cada INTERVALO_S segundos, para a pasta
# que o worker lê (PLANILHAS_DIR). O rclone preserva a data de modificação dos arquivos: o worker usa essa data para
# esperar a planilha terminar de sincronizar e para saber o que mudou.
# Roda no container "planilhas" do docker-compose.prod.yml (perfil "drive"); configuração em docs/03_DEPLOY_VPS.md.
set -eu

INTERVALO_S="${INTERVALO_S:-600}"

while true; do
    echo "$(date '+%F %T') planilhas: sincronizando ${RCLONE_ORIGEM}"
    # --include: só as planilhas do boletim (o mesmo padrão de nome que o adapter lê); o resto do Drive não vem
    rclone sync "${RCLONE_ORIGEM}" /dados/planilhas \
        --config /config/rclone/rclone.conf \
        --include "RELAT*.xls[xm]" --ignore-case \
        --drive-scope drive.readonly \
        --log-level NOTICE || echo "$(date '+%F %T') planilhas: falhou; tenta de novo na próxima volta"
    sleep "${INTERVALO_S}"
done

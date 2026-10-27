#!/bin/bash
# Backup do banco do Terra: um pg_dump por dia (formato custom, que o pg_restore lê), guardado em /backups, e os mais
# velhos que DIAS_DE_BACKUP apagados. Roda no container "backup" do docker-compose.prod.yml, em laço.
# Restaurar: ver docs/03_DEPLOY_VPS.md, "Backup e restauração".
set -euo pipefail

HORA_DO_BACKUP="${HORA_DO_BACKUP:-03:00}"
DIAS_DE_BACKUP="${DIAS_DE_BACKUP:-14}"

fazer_backup() {
    local arquivo="/backups/terra-$(date +%Y%m%d-%H%M).dump"
    echo "$(date '+%F %T') backup: gravando ${arquivo}"
    # grava num temporário e só renomeia no fim: um backup interrompido nunca parece completo
    pg_dump --format=custom --file="${arquivo}.parcial"
    mv "${arquivo}.parcial" "${arquivo}"
    find /backups -name 'terra-*.dump' -mtime +"${DIAS_DE_BACKUP}" -print -delete
    echo "$(date '+%F %T') backup: pronto ($(du -h "${arquivo}" | cut -f1))"
}

segundos_ate_o_proximo() {
    local agora proximo
    agora=$(date +%s)
    proximo=$(date -d "today ${HORA_DO_BACKUP}" +%s)
    if [ "${proximo}" -le "${agora}" ]; then
        proximo=$(date -d "tomorrow ${HORA_DO_BACKUP}" +%s)
    fi
    echo $((proximo - agora))
}

# o primeiro backup sai na subida do container, para já existir um logo depois do deploy
fazer_backup
while true; do
    sleep "$(segundos_ate_o_proximo)"
    fazer_backup
done

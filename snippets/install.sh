#!/bin/sh
SRC="$(dirname "$(readlink -f "$0")")"
DST=/etc/systemd/system
BIN=/usr/bin
SERVICE_FILES=(jupyter-vnc.service nginx-jupyter.service)
PORT_DIR=/etc/port-forward
PORT_SH=port-forward.sh
PORT_SERVICE=port-forward@.service

verbose=0
force=0
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -v|--verbose)
    verbose=1
    ;;
    -f|--force)
    force=1
    ;;
    *)
    ;;
  esac
  shift
done

debug() { if [ $verbose -eq 1 ]; then echo "[debug] $@"; fi; }
info() { echo "[info]  $@"; }
would() {
  if [ $force -eq 1 ]; then
    echo "[do]    $@"
    $@
    return $?
  fi
  echo "[would] $@"
  return 0
}

debug "force:$force" "verbose:$verbose"

check() {
  debug "check $1, $2"
  [ ! -f "$2" -o "$1" -nt "$2" ]
}

update() {
  if check "$SRC/$1" "$DST/$1"; then
    info "updating $SRC/$1"
    would cp "$SRC/$1" "$DST/"
    return 0
  fi
  debug "do not need update"
  return 1
}

check_service() {
  would systemctl status "$1"
  return $?
}

reload() {
  would systemctl restart "$1"
  would systemctl status "$1"
}

for service_file in ${SERVICE_FILES[@]}; do
  if update "$service_file"; then
    would systemctl daemon-reload
    reload "$service_file"
  fi
done

update_port=false
if [ ! -f "$BIN/$PORT_SH" ]; then
  info "install port sh to path"
  would ln -s "$SRC/$PORT_SH" "$BIN/"
  update_port=true
fi

if check "$SRC/$PORT_SH" "$SRC/$PORT_SERVICE"; then
  info "port sh updated, force push"
  would touch "$SRC/$PORT_SERVICE"
fi
if update "$PORT_SERVICE"; then
  debug "update_port set to true"
  would systemctl daemon-reload
  update_port=true
fi

debug "update_port:" $update_port
for port_file in "$SRC"/*.config; do
  port_file_base=$(basename "$port_file")
  should_reload=$update_port
  if check "$port_file" "$PORT_DIR/$port_file_base"; then
    info "updating port $port_file"
    would cp "$port_file" "$PORT_DIR/"
    should_reload=true
  fi
  if [[ "$should_reload" == "true" ]]; then
    reload "${PORT_SERVICE%.service}${port_file_base%.config}"
  fi
done

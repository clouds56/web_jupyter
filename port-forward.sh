#!/bin/zsh
# bash is stupid here for arrays
# if you are using bash, DO NOT have "space" in other_options

verbose=0
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --verbose)
    verbose=1
    ;;
    --port-config)
    source "$2" || exit 1
    shift
    ;;
    --forward)
    forward="$2"
    shift # past argument
    ;;
    --local_port)
    local_port="$2"
    shift # past argument
    ;;
    --local_addr)
    local_addr="$2"
    shift # past argument
    ;;
    --remote_port)
    remote_port="$2"
    shift # past argument
    ;;
    --remote_addr)
    remote_addr="$2"
    shift # past argument
    ;;
    --identity_file)
    identity_file="$2"
    shift # past argument
    ;;
    --target_host)
    target_host="$2"
    shift # past argument
    ;;
    --target_port)
    target_port="$2"
    shift # past argument
    ;;
    *)
    other_cmdlines+=($key)
    ;;
esac
shift # past argument or value
done

info() { if [ $verbose -eq 1 ]; then >&2 echo "$@"; fi }
warning() { >&2 echo $@; }
dump() {
  local arg_string="$1"
  shift
  for arg in "$@"; do arg_string+=" *$arg*"; done
  info "$arg_string"
}

dump "other arguments:" ${other_arguments[@]}
dump "other options:" ${other_options[@]}
dump "other cmdline:" ${other_cmdlines[@]}

for other_argument in ${other_arguments[@]}; do
  args+=($other_argument)
done

for other_option in ${other_options[@]}; do
  args+=(-o $other_option)
done

for other_cmdline in ${other_cmdlines[@]}; do
  args+=($other_cmdline)
done

if [[ "$forward" == "remote" ]]; then forward=-R; fi
if [[ "$forward" == "local" ]]; then forward=-L; fi

if [[ "$forward" == "-R" ]]; then
  if [[ "$local_port" == "" ]]; then
    warning "local_port not set when forward is remote"
    exit 1
  fi
  if [[ "$remote_port" == "" ]]; then
    remote_port="$local_port"
  fi
  if [[ "$local_addr" == "" ]]; then
    local_addr=localhost
  fi
  if [[ "$remote_addr" != "" ]]; then
    remote_addr+=":"
  fi
  args+=($forward $remote_addr$remote_port":"$local_addr":"$local_port)
fi

if [[ "$forward" == "-L" ]]; then
  if [[ "$remote_port" == "" ]]; then
    warning "remote_port not set when forward is remote"
    exit 1
  fi
  if [[ "$local_port" == "" ]]; then
    local_port="$remote_port"
  fi
  if [[ "$remote_addr" == "" ]]; then
    remote_addr=localhost
  fi
  if [[ "$local_addr" != "" ]]; then
    $local_addr+=":"
  fi
  args+=($forward $local_addr$local_port":"$remote_addr":"$remote_port)
fi

if [[ "$identity_file" != "" ]]; then
  args+=(-i $identity_file)
fi

if [[ "$target_host" != "" ]]; then
  args+=($target_host)
fi

if [[ "$target_port" != "" ]]; then
  args+=(-p $target_port)
fi

dump "would run " "${args[@]}"
ssh "${args[@]}"

#!/run/current-system/sw/bin/zsh

## remember to add something like the following to your .zshrc or
## equivalent shell environment file
#
# fpath=(~/dev/tpv.github/zsh-completions.d $fpath)
# export fpath

zshdir=$(pwd)/zsh-completion.d

[ -d $zshdir ] || mkdir $zshdir
./bin/gh --help-zsh-comp > $zshdir/_gh

reload() {
  local f
  f=($zshdir/*(.))
  unfunction $f:t 2> /dev/null
  autoload -U $f:t
}
reload

# fpath=($zshdir $fpath)
# export fpath


# .NET. A distro package (Fedora's dotnet-host) installs /usr/bin/dotnet with its
# own runtime root, so DOTNET_ROOT must stay unset there: pointing it at ~/.dotnet
# would hide the runtime from dotnet tools. Only a user-local SDK (the
# dotnet-install script, which puts everything in ~/.dotnet) needs it.
if [[ -x ~/.dotnet/dotnet ]]; then
  export DOTNET_ROOT=~/.dotnet
  path+=(~/.dotnet)
fi
# `dotnet tool install -g` puts tools here.
path+=(~/.dotnet/tools(N-/))

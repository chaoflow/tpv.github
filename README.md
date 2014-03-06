tpv.github
==========

tpv adaptor for github


Setup dev environment
---------------------

The dev environment requires the [nix package manager](http://nixos.org/nix/manual/).

```
% git clone git@github.com:chaoflownet/tpv.github.git
% git clone git@github.com:chaoflow/metachao.git
% git clone git@github.com:chaoflow/plumbum.git --branch completion
% git clone git@github.com:chaoflow/tpv.cli.git --branch completion
% git clone git@github.com:chaoflow/tpv.git
% cd tpv.github
% make bootstrap
% make
```

This should result in a successful run of tests.

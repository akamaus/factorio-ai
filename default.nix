{ pkgs ? import <nixpkgs> {}
, stdenv ? pkgs.stdenv
} :

let
 self = pkgs.python3Packages;
 overrides = self.callPackage ./overrides.nix {};
 spacy_russian_tokenizer = self.callPackage ./spacy_russian_tokenizer.nix {};

 pythonEnv = (pkgs.python3.withPackages
  (ps: with ps;
  [
    ipython
    jupyter
    matplotlib
    numpy
    tqdm
    z3
  ]));

 python_env_link_dir = "python-env";

 shellHook = ''
if [ -d ${python_env_link_dir} ]
then
  echo "Remove old link: ${python_env_link_dir}"
  rm ${python_env_link_dir};
fi

echo Create symbolic link ${python_env_link_dir} to ${pythonEnv}
ln -s ${pythonEnv} ${python_env_link_dir}
'';

in pythonEnv.env.overrideAttrs (x: { shellHook = shellHook; })

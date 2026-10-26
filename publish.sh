#!/bin/bash
# Publishes the suite-kit and releases every app that moved to it. Run once github.com/Quezka/suite-kit exists.
# Order matters: the kit first (CI installs it by tag), then each app: merge its suite-kit branch, push, tag.
set -e
cd "$(dirname "$0")/.."
git ls-remote git@github.com:Quezka/suite-kit.git >/dev/null 2>&1 || { echo "github.com/Quezka/suite-kit does not exist yet"; exit 1; }
(cd suite-kit && git remote get-url origin >/dev/null 2>&1 || git remote add origin git@github.com:Quezka/suite-kit.git
 git push origin main && git push origin --tags)
for app in gantry ligature folio bivouac facet quire; do
  (cd $app
   git checkout -q main && git merge -q --no-edit suite-kit
   v=$(python3 -c "import re;print(re.search(r'__version__ = \"([^\"]+)\"',open('$app/__init__.py').read()).group(1))")
   git push origin main && git tag -a "v$v" -m "$app $v" && git push origin "v$v"
   echo "$app $v pushed")
done
echo "missive has no remote yet: create github.com/Quezka/missive, then: cd missive && git remote add origin git@github.com:Quezka/missive.git && git push -u origin main"

#!/bin/sh
# Minimal installation file for sunny-cp.

echo -n 'Testing Python installation...'
which python 1>/dev/null
ret=$?
if 
  [ $ret -ne 0 ]
then
  echo 'Error! Python not properly installed'
  echo 'Aborted.'
  exit $ret
fi
echo 'OK!'

psv=`python -c "import psutil ; print (psutil.__version__[0])"` 2>/dev/null
if 
  [ -z $psv ]
then
  echo 'Error! Python psutil package not properly installed'
  echo 'Aborted.'
  exit 1
elif
  [ $psv -lt 2 ]
then
  echo 'Error! Python psutil package obsolete (need version >= 2.x)'
  echo 'Aborted.'
  exit 1
fi

psv=`python -c "import click"`
ret=$?
if 
  [ $ret -ne 0 ]
then
  echo 'Error! Python click package not properly installed'
  echo 'Aborted.'
  exit 1
fi

echo -n 'Testing MiniZinc installation...'
which minizinc 1>/dev/null
ret=$?
if 
  [ $ret -ne 0 ]
then
  echo 'Error! MiniZinc not properly installed'
  echo 'Aborted.'
  exit $ret
fi
echo 'OK!'

echo -n 'Testing mzn2feat installation...'
which mzn2feat 1>/dev/null
ret=$?
if 
  [ $ret -ne 0 ]
then
  echo 'Error! mzn2feat not properly installed'
  echo 'Aborted.'
  exit $ret
fi
echo 'OK!'

echo 'Adding solvers to the portfolio...'
python solvers/make_pfolio.py
ret=$?
if
  [ $ret -ne 0 ]
then
  echo 'Aborted.'
  exit $ret
fi
echo 'OK!'

echo 'Compiling python sources...'
for f in `find src -name *.py` `find kb -name *.py` ./bin/sunny-cp
do
  echo -n 'Compiling '$f'...'
  python $f --help 1>/dev/null
  ret=$?
  if 
    [ $ret -ne 0 ]
  then
    echo 'Error! '$f' not successfully compiled!'
    echo 'Aborted.'
    rm `find . -name *.pyc`
    exit $ret
  fi
  echo 'OK!'
done

export SUNNY_HOME=$PWD
cd $SUNNY_HOME

echo "--- Everything went well!"
echo "To complete sunny-cp installation just append $PWD/bin to the PATH" \
     "environment variable."

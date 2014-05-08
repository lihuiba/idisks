#!/bin/bash


function mydir {
	echo $(dirname "$(readlink -f "$0")")
}

function get_fullpath() 
{
  (
   if [ -d "$1" ]; then
      cd $1
   elif [[ -f "$1" || -L "$1" ]]; then
      cd `dirname "$1"`
   else
      echo "what it is?"
      cd
   fi
   echo `pwd`/`basename "$1"`
  )
}


if [[ $# = 0 || $1 = "-h" || $1 = "--help" ]]; then
	echo $0 node disk backing-store [directory]
	exit 0
fi

node=$1
disk=$2
store=`get_fullpath $3`
dir=${4:-`mydir`/targets.d}

echo "node: $node"
echo "disk: $disk"
echo "store: $store"
echo "dir: $dir"

if [ ! -e "$store" ] || [ -d "$store" ]; then
	echo "backing store NOT exists: '$store'"
	exit 1
fi

dir=$dir/$node
if [ ! -d "$dir" ]; then
	echo "config directory NOT exists: '$dir'"
	exit 1
fi

cfile=$dir/$disk
echo "cfile: $cfile"
if [[ -f "$cfile" || -L "$cfile" ]]; then
	echo "config file ALREADY exists: '$cfile'"
	exit 1
fi

set -x
cd $dir
ln $store $disk -s


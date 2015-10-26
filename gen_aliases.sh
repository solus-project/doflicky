#!/bin/bash

function do_fail()
{
    echo "Failure: $*"
    exit 1
}

# non-gpu packages behave.
pkgs=(  broadcom-sta )

WDIR="$(realpath ./work)"
ADIR="$(realpath ./aliases)"
MINFO="/sbin/modinfo"

if [[ -d "${WDIR}" ]]; then
    echo "Purging ${WDIR}"
    rm -rvf "${WDIR}" || do_fail "Unable to purge workdir"
fi
if [[ -d "${ADIR}" ]]; then
    echo "Purging ${ADIR}"
    rm -rvf "${ADIR}" || do_fail "Unable to purge aliasdir"
fi

mkdir "${WDIR}"
mkdir "${ADIR}"

pushd "${WDIR}" >/dev/null

for pkg in ${pkgs[*]} ; do
    mkdir "${pkg}"
    pushd "${pkg}" >/dev/null
    echo $pkg


    eopkg fetch "${pkg}" || do_fail "Unable to fetch ${pkg}"
    unpisi *.eopkg >/dev/null|| do_fail "Unable to extract eopkg"

    aliases=()
    modulen=""
    for module in `find install -name "*.ko"` ; do
        modulen="$(basename ${module})"
        modulen="${modulen%.*}"
        echo "Analysing ${module}"
        while read line ; do
            key="$(echo ${line}|awk -F : '{print $1}')"
            value="$(echo ${line}|awk '{print $2}')"
            if [[ "${key}" != "alias" ]]; then
                continue
            fi
            aliases+=("${value}")
        done < <("${MINFO}" "${module}")
    done

    echo "Aliases: ${aliases[*]}"

    if [[ ${#aliases[@]} -lt 1 ]]; then
        do_fail "No modaliases found for ${pkg}"
    fi

    for alias in ${aliases[*]} ; do
        echo "alias ${alias} ${modulen} ${pkg}" >> "${ADIR}/${pkg}.modaliases"
    done

    popd >/dev/null
done

popd >/dev/null

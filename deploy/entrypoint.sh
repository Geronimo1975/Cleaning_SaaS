#!/bin/sh
# Punctul de intrare al containerului `web`.
#
# `collectstatic` rulează și la build, dar volumul `staticfiles` e creat la
# prima pornire și de atunci UMBREȘTE conținutul imaginii: o imagine nouă cu
# fișiere statice noi nu le mai poate scrie acolo. Efectul e tăcut și
# înșelător — aplicația pornește, doar CSS-ul nou dă 404.
#
# De aceea se colectează la fiecare pornire, în volum.
set -e

python manage.py collectstatic --noinput --verbosity 0
exec "$@"

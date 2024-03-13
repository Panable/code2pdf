#!/bin/sh

clean.sh
python main.py ~/Homework/Data-Visualisation
pdftk extra/Lab10.pdf full.pdf cat output fullx.pdf
rm full.pdf
mv fullx.pdf full.pdf
pdftk full.pdf cat 1-r2 output fullx.pdf
rm full.pdf
mv fullx.pdf full.pdf

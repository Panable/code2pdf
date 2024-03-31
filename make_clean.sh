#!/bin/sh

clean.sh
python main.py ~/Homework/Data-Visualisation/labsubmission2
pdftk full.pdf ~/Homework/Data-Visualisation/labsubmission2/Lab-4-1/lab4-1.pdf cat output fullx.pdf
rm full.pdf
mv fullx.pdf full.pdf
# pdftk full.pdf cat 1-r2 output fullx.pdf
# rm full.pdf
# mv fullx.pdf full.pdf

import csv

data = [
    (1, "USV/c", "", "Ellipse green"),
    (2, "USV/n", "", "Hexagon green"),
    (3, "USV/s", "", "Parallelogram blue"),
    (4, "USD", "", "Rectangle orange"),
    (5, "VSF", "", "Hoctagon black"),
    (6, "SFF", "", "Hoctagon white"),# nel campo tipo dell template si scriverà SFF ma verrà stampato SF per questioni di ambiguità con VSF
    (7, "US", "", "Rectangle red"),
    (8, "USM", "", "Rectangle red"),
    (9, "US/s", "", "Ellipse red"),
    (10, "USM/s", "", "Ellipse red"),
    (11, "UTR", "", "rectangle dot red"),
    (12, "property", "", ""),
    (11, "document", "", ""),
    (13, "combiner", "", ""),
    (14, "extractor", "", ""),
    (15, "continuity", "", ""),
   ]


with open("../unita_tipo.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Indice", "TIPO", "Descrizione", "Simbolo"])
    writer.writerows(data)
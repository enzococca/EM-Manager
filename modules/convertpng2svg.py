import cv2
import svgwrite
from pathlib import Path


def find_contours(binary_image):
    # Trova i contorni nell'immagine binaria
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def draw_svg(contours, output_svg_path):
    # Create a new SVG file
    dwg = svgwrite.Drawing(output_svg_path, profile='tiny')

    # Draw every contour found in the image
    for contour in contours:
        # Create a SVG path for the contour points
        path = svgwrite.path.Path(stroke='black', fill='none')
        first_point = True
        for point in contour:
            # Flatten the point array and extract x, y coordinates
            x, y = point.ravel()
            if first_point:
                path.push('M', x, y)
                first_point = False
            else:
                path.push('L', x, y)
        path.push('Z')
        dwg.add(path)

    # Save the SVG file
    dwg.save()


def vectorize_image(image_path, output_svg_path):
    # Leggi l'immagine in scala di grigi
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    # Applica un threshold per ottenere una immagine binaria
    # Qui è possibile regolare il valore di thresholding per catturare meglio i contorni
    _, binary_image = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Trova i contorni nell'immagine binaria
    contours = find_contours(binary_image)

    # Disegna i contorni in un file SVG
    draw_svg(contours, output_svg_path)


# Percorso della cartella contenente le immagini PNG
input_directory = Path('icons')

# Percorso della cartella in cui verranno salvati i file SVG
output_directory = Path('icons')
output_directory.mkdir(exist_ok=True)

# Esegui la vettorializzazione per ogni file PNG nella directory
for image_path in input_directory.glob('*.png'):
    output_svg_path = output_directory / (image_path.stem + '.svg')
    vectorize_image(image_path, output_svg_path)
    print(f"Vettorializzato: {image_path} -> {output_svg_path}")

from tools.multimodal_query import NomicVisionQuerier
from config import RETRIEVED_IMAGES_PATH, INPUT_PDF_FOLDER
import os

def test_image_extraction():
    print("\n=== Testing Image Extraction ===\n")
    
    # Initialize the querier
    print("Initializing NomicVisionQuerier...")
    querier = NomicVisionQuerier()
    
    # Debugging: Check if the image directory path exists
    print(f"Checking if image directory path exists: {RETRIEVED_IMAGES_PATH}")
    print(f"Image directory exists: {RETRIEVED_IMAGES_PATH.exists()}")
    
    # Print image directory information
    if RETRIEVED_IMAGES_PATH.exists():
        print(f"\nImage Directory:")
        print(f"Path: {RETRIEVED_IMAGES_PATH}")
        print(f"Exists: {RETRIEVED_IMAGES_PATH.exists()}")
    else:
        print("Image directory does not exist")
    
    # Test with a sample PDF
    test_pdf = INPUT_PDF_FOLDER / "IIM_2024-15.pdf"  # Replace with an actual PDF path
    print(f"\nTesting PDF extraction:")
    print(f"PDF Path: {test_pdf}")
    
    # Debugging: Check if the PDF path exists
    print(f"Checking if PDF path exists: {os.path.exists(test_pdf)}")
    
    if os.path.exists(test_pdf):
        print("PDF file exists, extracting images...")
        for page_num in range(1, 4):  # Test first 3 pages
            print(f"\nProcessing page {page_num}:")
            images = querier.extract_images_from_pdf(test_pdf, page_num)
            print(f"Found {len(images)} images on page {page_num}")
            for img_path in images:
                print(f"  - {img_path}")
    else:
        print("Please provide a valid PDF path to test image extraction")
    
    # Print contents of image directory
    print("\nContents of image directory:")
    if RETRIEVED_IMAGES_PATH.exists():
        files = list(RETRIEVED_IMAGES_PATH.glob('*.png'))
        print(f"Found {len(files)} image files:")
        for file in files:
            print(f"  - {file.name}")
    else:
        print("Image directory does not exist")

if __name__ == "__main__":
    test_image_extraction()
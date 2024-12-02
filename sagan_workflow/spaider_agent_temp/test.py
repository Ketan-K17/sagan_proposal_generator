from tools.multimodal_query import NomicVisionQuerier
from config import RETRIEVED_IMAGES_PATH
import os

def test_image_extraction():
    print("\n=== Testing Image Extraction ===\n")
    
    # Initialize the querier
    print("Initializing NomicVisionQuerier...")
    querier = NomicVisionQuerier()
    
    # Print image directory information
    print(f"\nImage Directory:")
    print(f"Path: {RETRIEVED_IMAGES_PATH}")
    print(f"Exists: {RETRIEVED_IMAGES_PATH.exists()}")
    
    # Test with a sample PDF
    test_pdf = "C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/sagan_multimodal/data/exploring-the-impact-of-hybrid-and-remote-work-models-on-business-efficiency-and-employee-well-being-a-scoping-review.pdf"  # Replace with an actual PDF path
    print(f"\nTesting PDF extraction:")
    print(f"PDF Path: {test_pdf}")
    
    if os.path.exists(test_pdf):
        print("PDF file exists, extracting images...")
        # Try to extract images from first few pages
        for page_num in range(3):  # Test first 3 pages
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
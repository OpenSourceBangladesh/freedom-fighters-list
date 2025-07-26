#!/usr/bin/env python3
"""
Run the Final Freedom Fighter Detail Scraper
Production script to scrape all fighters from fflist.csv
"""

import sys
import time
from final_detail_scraper import FinalFreedomFighterDetailScraper

def main():
    """Main function to run the full scraper"""
    
    print("=" * 60)
    print("🚀 Starting Final Freedom Fighter Detail Scraper")
    print("=" * 60)
    
    # Check if CSV file exists
    csv_file = "fflist.csv"
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            pass
    except FileNotFoundError:
        print(f"❌ Error: {csv_file} not found!")
        print("Please make sure fflist.csv is in the current directory.")
        sys.exit(1)
    
    # Initialize scraper
    print("🔧 Initializing scraper...")
    scraper = FinalFreedomFighterDetailScraper(csv_file)
    
    # Configure scraping parameters
    MAX_WORKERS = 20  # Maximum concurrent connections for speed
    DELAY_BETWEEN_REQUESTS = 0.1  # 0.1 seconds between requests
    
    print(f"⚙️  HIGH-SPEED Configuration:")
    print(f"   Max Workers: {MAX_WORKERS} (Maximum concurrency)")
    print(f"   Delay Between Requests: {DELAY_BETWEEN_REQUESTS} seconds (Minimal delay)")
    print(f"   Connection Pool: 100 connections per worker")
    print(f"   Timeout: 15 seconds per request")
    print(f"   Progress Save: Every 50 completions")
    print(f"   Output Directory: fighters/")
    
    # Show folder structure
    print(f"\n📁 Folder Structure:")
    print(f"   fighters/ - JSON files for each fighter")
    print(f"   detail_scraping_progress.json - Progress tracking")
    
    # Show JSON structure
    print(f"\n📄 JSON Structure:")
    print(f"   fighter_number - Fighter ID")
    print(f"   detail_url - Original detail page URL")
    print(f"   fighter_photo_url - Fighter photo URL (if available)")
    print(f"   basic_info - Name, district, upazila, etc.")
    print(f"   prove_documents - Supporting documents")
    print(f"   waris_info - Heir information with photo URLs")
    print(f"   scraped_at - Timestamp")
    
    # Ask for confirmation
    print(f"\n⚠️  This will scrape detailed information for all fighters in {csv_file}")
    print("   This may take several hours to complete.")
    print("   Only data will be scraped - no photos will be downloaded.")
    print("   Photo URLs will be saved in JSON files for later download.")
    
    while True:
        response = input("\n🤔 Do you want to continue? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            break
        elif response in ['n', 'no']:
            print("❌ Scraping cancelled.")
            sys.exit(0)
        else:
            print("Please enter 'y' for yes or 'n' for no.")
    
    # Start scraping
    print(f"\n🚀 Starting scraper...")
    print("💡 You can stop the scraper anytime with Ctrl+C")
    print("💡 Progress will be saved and you can resume later")
    print("💡 Check detail_scraping_progress.json for current progress")
    
    try:
        start_time = time.time()
        
        # Run the scraper
        scraper.run_scraper(
            max_workers=MAX_WORKERS,
            delay_between_requests=DELAY_BETWEEN_REQUESTS
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n🎉 Scraping completed!")
        print(f"⏱️  Total time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        
        # Final statistics
        print(f"\n📊 Final Results:")
        scraper.print_statistics()
        
    except KeyboardInterrupt:
        print(f"\n\n⏸️  Scraping interrupted by user")
        print("💾 Progress has been saved to detail_scraping_progress.json")
        print("🔄 You can resume by running this script again")
        scraper.save_progress()
        scraper.print_statistics()
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        scraper.save_progress()
        scraper.print_statistics()
        sys.exit(1)

if __name__ == "__main__":
    main()

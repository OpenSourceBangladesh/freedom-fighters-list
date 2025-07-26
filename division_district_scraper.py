import requests
import json
import csv
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import urllib3
import os
from datetime import datetime
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DivisionDistrictScraper:
    def __init__(self):
        self.session = requests.Session()
        self.csv_file = '../freedom_fighters_data.csv'
        self.progress_file = 'division_district_progress.json'
        self.existing_fighters = set()
        self.csv_lock = threading.Lock()
        self.progress_lock = threading.Lock()
        
        # Load location data
        with open('location_data_complete.json', 'r', encoding='utf-8') as f:
            self.location_data = json.load(f)
        
        # Load progress if exists
        self.progress = self.load_progress()
        
        # Load existing fighter numbers from CSV
        self.load_existing_fighters()
    
    def load_existing_fighters(self):
        """Load existing freedom fighter numbers to avoid duplicates"""
        if os.path.exists(self.csv_file):
            try:
                with open(self.csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        fighter_num = row.get('মুক্তিযোদ্ধার নম্বর', '').strip()
                        if fighter_num:
                            self.existing_fighters.add(fighter_num)
                print(f"Loaded {len(self.existing_fighters)} existing fighter records from CSV")
            except Exception as e:
                print(f"Error loading existing data: {e}")
    
    def load_progress(self):
        """Load scraping progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading progress: {e}")
        
        return {
            'completed_combinations': {},  # Format: {"div_id-dist_id": {"last_page": 5, "total_pages": 10, "completed": False}}
            'new_records_found': 0,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'current_combination': ''
        }
    
    def save_progress(self, combination_key, page_number, total_pages=None, completed=False, new_records=0):
        """Save scraping progress"""
        with self.progress_lock:
            if combination_key not in self.progress['completed_combinations']:
                self.progress['completed_combinations'][combination_key] = {
                    'last_page': 0,
                    'total_pages': 0,
                    'completed': False
                }
            
            self.progress['completed_combinations'][combination_key]['last_page'] = page_number
            if total_pages:
                self.progress['completed_combinations'][combination_key]['total_pages'] = total_pages
            if completed:
                self.progress['completed_combinations'][combination_key]['completed'] = True
            
            self.progress['new_records_found'] += new_records
            self.progress['last_update'] = datetime.now().isoformat()
            self.progress['current_combination'] = combination_key
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def generate_combinations(self):
        """Generate all division-district combinations"""
        combinations = []
        
        for div_id, div_name in self.location_data['divisions'].items():
            if div_id not in self.location_data['districts']:
                continue
                
            for dist_id, dist_name in self.location_data['districts'][div_id].items():
                combination_key = f"{div_id}-{dist_id}"
                
                # Check if already completed
                if (combination_key in self.progress['completed_combinations'] and 
                    self.progress['completed_combinations'][combination_key].get('completed', False)):
                    continue
                
                # Get starting page if resuming
                start_page = 1
                if combination_key in self.progress['completed_combinations']:
                    start_page = self.progress['completed_combinations'][combination_key]['last_page'] + 1
                
                combinations.append({
                    'key': combination_key,
                    'division_id': div_id,
                    'division_name': div_name,
                    'district_id': dist_id,
                    'district_name': dist_name,
                    'start_page': start_page
                })
        
        return combinations
    
    def get_page_results(self, combination, page=1):
        """Get results for a specific page of a combination"""
        url = "https://mis.molwa.gov.bd/freedom-fighter-list"
        
        params = {
            'division_id': combination['division_id'],
            'district_id': combination['district_id'],
            'thana_id': '',  # Empty to get all upazilas in the district
            'prove_type': '',  # Empty to get all prove types
            'name': '',
            'gazette_no': '',
            'beneficiary_code': '',
            'page': page
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = self.session.get(url, params=params, headers=headers, 
                                      timeout=30, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching page {page} for {combination['key']}: {e}")
            return None
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', str(text).strip())
        return text
    
    def extract_fighters_from_html(self, html_content, combination):
        """Extract freedom fighter data from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        fighters = []
        total_count = 0
        
        try:
            # Find the table with freedom fighter data
            table = soup.find('table', class_='table')
            if not table:
                return fighters, 0, False
            
            # Find tbody and get rows safely
            tbody = table.find('tbody')
            rows = []
            if tbody and str(type(tbody)) != "<class 'bs4.element.NavigableString'>":
                try:
                    rows = tbody.find_all('tr')
                except:
                    pass
            
            if not rows:
                return fighters, 0, False
            
            # Get total count from pagination info if available
            pagination_info = soup.find('div', class_='dataTables_info')
            if pagination_info:
                text = pagination_info.get_text()
                # Extract total count from text like "Showing 1 to 10 of 57 entries"
                match = re.search(r'of (\d+) entries', text)
                if match:
                    total_count = int(match.group(1))
            
            # Check if there are more pages - simplified approach
            has_more_pages = False
            next_links = soup.find_all('a', string='Next')
            if next_links:
                # If we find a "Next" link, assume there are more pages
                has_more_pages = True
            # Alternative: check if we got a full page of results (assuming 10 per page)
            elif len(rows) >= 10:
                has_more_pages = True
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 7:  # Ensure we have enough columns
                    try:
                        fighter_number = self.clean_text(cells[1].get_text())
                        name = self.clean_text(cells[2].get_text())
                        father_name = self.clean_text(cells[3].get_text())
                        living_status = self.clean_text(cells[4].get_text())
                        village = self.clean_text(cells[5].get_text())
                        post_office = self.clean_text(cells[6].get_text())
                        
                        # Skip if this fighter already exists in our CSV
                        if fighter_number in self.existing_fighters:
                            continue
                        
                        # Try to determine upazila from the address or other info
                        upazila_name = "Unknown"
                        # Look for upazila info in additional cells if available
                        if len(cells) > 8:
                            upazila_info = self.clean_text(cells[8].get_text())
                            if upazila_info:
                                upazila_name = upazila_info
                        
                        # Get details link if available
                        details = ""
                        details_link = cells[7].find('a') if len(cells) > 7 else None
                        if details_link and details_link.get('href'):
                            details = f"https://mis.molwa.gov.bd{details_link.get('href')}"
                        
                        fighter_data = {
                            'মুক্তিযোদ্ধার নম্বর': fighter_number,
                            'নাম': name,
                            'পিতার নাম': father_name,
                            'জীবিত কি না?': living_status,
                            'গ্রাম/মহল্লা': village,
                            'ডাকঘর': post_office,
                            'উপজেলা': upazila_name,
                            'জেলা': combination['district_name'],
                            'বিভাগ': combination['division_name'],
                            'তালিকা': 'District Level Search',
                            'বিস্তারিত': details
                        }
                        
                        fighters.append(fighter_data)
                        # Add to existing fighters set to avoid duplicates within this session
                        self.existing_fighters.add(fighter_number)
                        
                    except Exception as e:
                        print(f"Error parsing row: {e}")
                        continue
            
            return fighters, total_count, has_more_pages
            
        except Exception as e:
            print(f"Error parsing HTML for {combination['key']}: {e}")
            return fighters, 0, False
    
    def save_fighters_to_csv(self, fighters):
        """Save fighters data to CSV file"""
        if not fighters:
            return
        
        with self.csv_lock:
            try:
                # Check if file exists to determine if we need headers
                file_exists = os.path.exists(self.csv_file)
                
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'মুক্তিযোদ্ধার নম্বর', 'নাম', 'পিতার নাম', 'জীবিত কি না?', 
                        'গ্রাম/মহল্লা', 'ডাকঘর', 'উপজেলা', 'জেলা', 'বিভাগ', 'তালিকা', 'বিস্তারিত'
                    ])
                    
                    # Write headers only if file is new
                    if not file_exists:
                        writer.writeheader()
                    
                    for fighter in fighters:
                        writer.writerow(fighter)
                        
                print(f"Saved {len(fighters)} new fighters to CSV")
                
            except Exception as e:
                print(f"Error saving to CSV: {e}")
    
    def process_combination(self, combination):
        """Process a single division-district combination and extract all fighters"""
        print(f"Processing: {combination['key']} ({combination['division_name']} > {combination['district_name']})")
        
        total_new_fighters = 0
        page = combination['start_page']
        has_more_pages = True
        total_pages_estimate = 0
        
        while has_more_pages:
            print(f"  Processing page {page}...")
            
            html_content = self.get_page_results(combination, page)
            if not html_content:
                break
            
            fighters, total_count, has_more_pages = self.extract_fighters_from_html(html_content, combination)
            
            # Calculate total pages estimate
            if total_count > 0 and total_pages_estimate == 0:
                total_pages_estimate = (total_count + 9) // 10  # Assuming 10 records per page
            
            if fighters:
                self.save_fighters_to_csv(fighters)
                total_new_fighters += len(fighters)
                print(f"  Page {page}: Found {len(fighters)} new fighters")
            else:
                if page == combination['start_page']:
                    print(f"  No new data found for combination: {combination['key']}")
            
            # Save progress for this page
            self.save_progress(combination['key'], page, total_pages_estimate, 
                             completed=not has_more_pages, new_records=len(fighters) if fighters else 0)
            
            if has_more_pages:
                page += 1
                time.sleep(0.8)  # Rate limiting between pages
            
            # Safety check: don't process more than 1000 pages for any combination
            if page > 1000:
                print(f"  Warning: Reached page limit (1000) for {combination['key']}")
                break
        
        print(f"Completed: {combination['key']} - New fighters found: {total_new_fighters}")
        return total_new_fighters
    
    def run_scraping(self, max_workers=8):
        """Run the scraping process with multiple threads"""
        combinations = self.generate_combinations()
        total_combinations_to_process = len(combinations)
        
        # Calculate total possible combinations
        total_possible_combinations = 0
        completed_combinations = 0
        for div_id in self.location_data['divisions']:
            if div_id in self.location_data['districts']:
                div_districts = len(self.location_data['districts'][div_id])
                total_possible_combinations += div_districts
                # Count completed combinations
                for dist_id in self.location_data['districts'][div_id]:
                    combination_key = f"{div_id}-{dist_id}"
                    if (combination_key in self.progress['completed_combinations'] and 
                        self.progress['completed_combinations'][combination_key].get('completed', False)):
                        completed_combinations += 1
        
        print(f"Starting division-district scraper")
        print(f"Total combinations to process: {total_combinations_to_process}")
        print(f"Already completed: {completed_combinations}/{total_possible_combinations}")
        print(f"Using {max_workers} concurrent workers")
        print(f"Existing fighters in CSV: {len(self.existing_fighters)}")
        
        if not combinations:
            print("All division-district combinations have been processed!")
            print(f"Final summary:")
            print(f"- Total combinations: {completed_combinations}/{total_possible_combinations}")
            print(f"- New records found: {self.progress['new_records_found']}")
            print(f"- Existing fighters: {len(self.existing_fighters)}")
            return
        
        start_time = time.time()
        total_new_records = 0
        completed_in_this_run = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all combinations
            future_to_combination = {
                executor.submit(self.process_combination, combo): combo 
                for combo in combinations
            }
            
            # Process results as they complete
            for future in as_completed(future_to_combination):
                combination = future_to_combination[future]
                try:
                    new_records = future.result()
                    total_new_records += new_records
                    completed_in_this_run += 1
                    
                    # Progress update
                    current_completed = completed_combinations + completed_in_this_run
                    print(f"Progress: {current_completed}/{total_possible_combinations} combinations completed ({completed_in_this_run}/{total_combinations_to_process} in this run)")
                    
                except Exception as e:
                    print(f"Error processing combination {combination['key']}: {e}")
                
                # Add delay between combinations to be respectful
                time.sleep(1.5)
        
        elapsed_time = time.time() - start_time
        print(f"\nDivision-district scraping completed!")
        print(f"Total time: {elapsed_time:.2f} seconds")
        print(f"Total new records found: {total_new_records}")
        print(f"Total existing fighters: {len(self.existing_fighters)}")
        print(f"CSV file: {self.csv_file}")

def main():
    scraper = DivisionDistrictScraper()
    scraper.run_scraping(max_workers=8)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple HTTP test to check login page structure
"""

import requests
import logging
from bs4 import BeautifulSoup
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_login_page_http():
    """Test the login page using HTTP requests"""
    try:
        # First, let's try the main domain
        logger.info("🌐 Checking main domain...")
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Try main domain first
        main_response = requests.get('https://booking.gopichandacademy.com/', 
                                   headers=headers, timeout=30)
        logger.info(f"📄 Main domain status: {main_response.status_code}")
        logger.info(f"📄 Main domain URL: {main_response.url}")
        
        if main_response.status_code == 200:
            # Parse main page to find login links
            main_soup = BeautifulSoup(main_response.content, 'html.parser')
            title = main_soup.find('title')
            logger.info(f"📄 Main page title: '{title.text if title else 'No title'}'")
            
            # Look for login-related links
            links = main_soup.find_all('a')
            login_links = []
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                if 'login' in href.lower() or 'login' in text or 'sign in' in text:
                    login_links.append((href, text))
            
            logger.info(f"🔗 Found {len(login_links)} potential login links:")
            for href, text in login_links:
                logger.info(f"  Link: '{text}' -> '{href}'")
            
            # Save main page content
            os.makedirs('data', exist_ok=True)
            with open('data/main_page_content.html', 'w', encoding='utf-8') as f:
                f.write(main_response.text)
            logger.info("💾 Main page content saved to data/main_page_content.html")
        
        # Now try login page
        logger.info("🌐 Fetching login page via HTTP...")
        response = requests.get('https://booking.gopichandacademy.com/login', 
                               headers=headers, timeout=30, allow_redirects=True)
        
        logger.info(f"📄 Response status: {response.status_code}")
        logger.info(f"📄 Response URL: {response.url}")
        logger.info(f"📄 Content length: {len(response.content)} bytes")
        logger.info(f"📄 Content type: {response.headers.get('content-type', 'unknown')}")
        
        # Check if we were redirected
        if response.url != 'https://booking.gopichandacademy.com/login':
            logger.info(f"🔄 Redirected to: {response.url}")
        
        if response.status_code == 200:
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get page title
            title = soup.find('title')
            logger.info(f"📄 Page title: '{title.text if title else 'No title'}'")
            
            # Count inputs
            inputs = soup.find_all('input')
            logger.info(f"📝 Found {len(inputs)} input elements:")
            
            for i, inp in enumerate(inputs):
                input_type = inp.get('type', 'no-type')
                input_name = inp.get('name', 'no-name')
                input_id = inp.get('id', 'no-id')
                input_placeholder = inp.get('placeholder', 'no-placeholder')
                logger.info(f"  Input #{i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
            
            # Count buttons
            buttons = soup.find_all('button')
            logger.info(f"🔘 Found {len(buttons)} button elements:")
            
            for i, btn in enumerate(buttons[:5]):  # Show first 5
                btn_text = btn.get_text(strip=True) or 'no-text'
                btn_id = btn.get('id', 'no-id')
                btn_class = btn.get('class', 'no-class')
                logger.info(f"  Button #{i+1}: text='{btn_text}', id='{btn_id}', class='{btn_class}'")
            
            # Count scripts (for dynamic content)
            scripts = soup.find_all('script')
            logger.info(f"🔧 Found {len(scripts)} script tags")
            
            # Look for iframes
            iframes = soup.find_all('iframe')
            logger.info(f"🖼️ Found {len(iframes)} iframe elements:")
            
            for i, iframe in enumerate(iframes):
                src = iframe.get('src', 'no-src')
                iframe_id = iframe.get('id', 'no-id')
                logger.info(f"  Iframe #{i+1}: src='{src}', id='{iframe_id}'")
            
            # Check for forms
            forms = soup.find_all('form')
            logger.info(f"📋 Found {len(forms)} form elements:")
            
            for i, form in enumerate(forms):
                action = form.get('action', 'no-action')
                method = form.get('method', 'no-method')
                form_id = form.get('id', 'no-id')
                logger.info(f"  Form #{i+1}: action='{action}', method='{method}', id='{form_id}'")
            
            # Save the HTML content for inspection
            os.makedirs('data', exist_ok=True)
            with open('data/http_login_page_content.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("💾 Page content saved to data/http_login_page_content.html")
            
            # Check for specific patterns that might indicate dynamic content
            if 'React' in response.text or 'vue' in response.text.lower() or 'angular' in response.text.lower():
                logger.info("⚡ Detected possible JavaScript framework - content might be dynamically loaded")
            
            if 'loading' in response.text.lower() or 'spinner' in response.text.lower():
                logger.info("🔄 Detected loading indicators in HTML")
            
        else:
            logger.error(f"❌ Failed to fetch page: HTTP {response.status_code}")
            
            # Save the error response for inspection
            os.makedirs('data', exist_ok=True)
            with open('data/http_error_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("💾 Error response saved to data/http_error_response.html")
            
            # Check what the 404 page contains
            if response.status_code == 404:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                logger.info(f"📄 404 Page title: '{title.text if title else 'No title'}'")
                logger.info(f"📄 404 Page content preview: {response.text[:200]}...")
            
    except Exception as e:
        logger.error(f"❌ Error during HTTP test: {e}")

if __name__ == "__main__":
    test_login_page_http()

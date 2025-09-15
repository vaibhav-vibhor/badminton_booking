#!/usr/bin/env python3
"""
Enhanced website structure analyzer
"""

import requests
import logging
from bs4 import BeautifulSoup
import os
import json
import re
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_website():
    """Analyze the website structure to find login functionality"""
    try:
        base_url = "https://booking.gopichandacademy.com"
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        logger.info(f"🌐 Analyzing website: {base_url}")
        
        # Try main domain
        response = requests.get(base_url, headers=headers, timeout=10)
        logger.info(f"📄 Main page status: {response.status_code}")
        logger.info(f"📄 Response headers: {dict(response.headers)}")
        logger.info(f"📄 Content-Type: {response.headers.get('content-type', 'unknown')}")
        logger.info(f"📄 Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Try different encodings
            content = None
            encoding_used = None
            
            # Try to decode with proper encoding
            encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1252', 'ascii']
            
            for encoding in encodings_to_try:
                try:
                    content = response.content.decode(encoding)
                    encoding_used = encoding
                    logger.info(f"✅ Successfully decoded with {encoding}")
                    break
                except UnicodeDecodeError:
                    logger.info(f"❌ Failed to decode with {encoding}")
                    continue
            
            if not content:
                # If all else fails, decode with errors='replace'
                content = response.content.decode('utf-8', errors='replace')
                encoding_used = 'utf-8 (with errors replaced)'
                logger.warning("⚠️ Using fallback decoding with error replacement")
            
            logger.info(f"📄 Using encoding: {encoding_used}")
            logger.info(f"📄 Content preview (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
            # Save raw content for inspection
            with open('data/website_analysis.html', 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("💾 Full content saved to data/website_analysis.html")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract key information
            title = soup.title.string if soup.title else "No title"
            logger.info(f"📄 Page title: '{title}'")
            
            # Look for JavaScript files that might handle routing
            scripts = soup.find_all('script')
            logger.info(f"🔧 Found {len(scripts)} script tags")
            
            for i, script in enumerate(scripts):
                if script.get('src'):
                    src = script['src']
                    if not src.startswith('http'):
                        src = urljoin(base_url, src)
                    logger.info(f"  Script {i+1}: {src}")
                elif script.string and len(script.string) > 50:
                    preview = script.string[:100].replace('\n', ' ').replace('\r', ' ')
                    logger.info(f"  Inline script {i+1}: {preview}...")
            
            # Look for meta tags
            metas = soup.find_all('meta')
            logger.info(f"📋 Found {len(metas)} meta tags")
            for meta in metas:
                if meta.get('name') or meta.get('property'):
                    name = meta.get('name') or meta.get('property')
                    content_attr = meta.get('content', '')
                    logger.info(f"  Meta: {name} = {content_attr}")
            
            # Look for links
            links = soup.find_all('link')
            logger.info(f"🔗 Found {len(links)} link tags")
            for link in links:
                if link.get('href') and link.get('rel'):
                    href = link['href']
                    rel = ' '.join(link['rel']) if isinstance(link['rel'], list) else link['rel']
                    logger.info(f"  Link: {rel} -> {href}")
            
            # Look for any forms
            forms = soup.find_all('form')
            logger.info(f"📝 Found {len(forms)} forms")
            for i, form in enumerate(forms):
                action = form.get('action', 'No action')
                method = form.get('method', 'GET')
                logger.info(f"  Form {i+1}: {method} {action}")
            
            # Look for divs with IDs (common in SPAs)
            divs_with_id = soup.find_all('div', id=True)
            logger.info(f"🏗️ Found {len(divs_with_id)} divs with IDs")
            for div in divs_with_id:
                logger.info(f"  Div ID: {div['id']}")
            
            # Check if this looks like a Single Page Application
            spa_indicators = [
                'react', 'vue', 'angular', 'vite', 'webpack',
                'app.js', 'main.js', 'bundle', 'chunk'
            ]
            
            is_spa = False
            spa_clues = []
            for indicator in spa_indicators:
                if indicator.lower() in content.lower():
                    spa_clues.append(indicator)
                    is_spa = True
            
            if is_spa:
                logger.info(f"🎯 This appears to be a Single Page Application (SPA)")
                logger.info(f"🔍 SPA indicators found: {', '.join(spa_clues)}")
            
            # Try common authentication endpoints
            auth_endpoints = [
                '/login',
                '/signin', 
                '/auth',
                '/authentication',
                '/user/login',
                '/account/login',
                '/api/auth',
                '/api/login'
            ]
            
            logger.info("🔐 Testing common authentication endpoints...")
            working_endpoints = []
            
            for endpoint in auth_endpoints:
                test_url = urljoin(base_url, endpoint)
                try:
                    test_response = requests.get(test_url, headers=headers, timeout=5)
                    logger.info(f"  {endpoint}: {test_response.status_code}")
                    if test_response.status_code == 200:
                        working_endpoints.append(endpoint)
                except Exception as e:
                    logger.info(f"  {endpoint}: Error - {str(e)[:50]}")
            
            if working_endpoints:
                logger.info(f"✅ Found working endpoints: {working_endpoints}")
            else:
                logger.info("❌ No working authentication endpoints found")
        
        else:
            logger.error(f"❌ Failed to fetch main page: HTTP {response.status_code}")
        
    except Exception as e:
        logger.error(f"❌ Error analyzing website: {str(e)}")
        raise

if __name__ == "__main__":
    analyze_website()

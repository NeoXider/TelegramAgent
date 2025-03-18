import logging
from typing import Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
from .base import BaseAgent
import os
from urllib.parse import urlparse, urljoin

class WebBrowserAgent(BaseAgent):
    """Agent for browsing websites and extracting content"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.screenshot_dir = os.path.join('data', 'temp', 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def visit_url(self, url: str, extract_images: bool = True) -> Dict[str, Any]:
        """
        Visit a URL and extract content
        
        Args:
            url: URL to visit
            extract_images: Whether to download images
            
        Returns:
            Dictionary containing page content and metadata
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title
                        title = soup.title.string if soup.title else ''
                        
                        # Extract main content
                        content = ''
                        for p in soup.find_all('p'):
                            content += p.get_text() + '\n'
                        
                        # Extract images if requested
                        images = []
                        if extract_images:
                            for img in soup.find_all('img'):
                                img_url = img.get('src')
                                if img_url:
                                    if os.path.exists(img_url):  # Локальный файл
                                        images.append(img_url)
                                    elif not img_url.startswith(('http://', 'https://')):
                                        img_url = urljoin(url, img_url)
                                        images.append(img_url)
                                    else:
                                        images.append(img_url)
                        
                        return {
                            'status': 'success',
                            'title': title,
                            'content': content.strip(),
                            'images': images,
                            'url': url
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f"Failed to load page: {response.status}"
                        }
                        
        except Exception as e:
            self.logger.error(f"Error visiting URL: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error visiting URL: {str(e)}"
            }
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming message and visit URL"""
        try:
            url = message.get('text', '')
            if not url:
                return {
                    'status': 'error',
                    'message': 'No URL provided'
                }
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            result = await self.visit_url(url)
            
            if result['status'] == 'error':
                return result
            
            # Format response
            response_text = f"Title: {result['title']}\n\n"
            response_text += f"Content:\n{result['content'][:1000]}...\n\n"
            
            if result['images']:
                response_text += f"Found {len(result['images'])} images on the page.\n"
            
            return {
                'status': 'success',
                'message': response_text,
                'data': result
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error processing URL: {str(e)}"
            } 
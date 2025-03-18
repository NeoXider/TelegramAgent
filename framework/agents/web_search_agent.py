import logging
from typing import Dict, Any, List
import aiohttp
from bs4 import BeautifulSoup
from .base import BaseAgent

class WebSearchAgent(BaseAgent):
    """Agent for performing web searches"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.search_engine = config.get('search_engine', 'https://www.google.com/search')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a web search and return results
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries containing search results
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': query,
                    'num': max_results
                }
                async with session.get(self.search_engine, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        results = []
                        
                        # Extract search results
                        for result in soup.select('div.g'):
                            title_elem = result.select_one('h3')
                            link_elem = result.select_one('a')
                            snippet_elem = result.select_one('div.VwiC3b')
                            
                            if title_elem and link_elem:
                                results.append({
                                    'title': title_elem.get_text(),
                                    'url': link_elem.get('href'),
                                    'snippet': snippet_elem.get_text() if snippet_elem else ''
                                })
                        
                        return results[:max_results]
                    else:
                        self.logger.error(f"Search failed with status code: {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error performing web search: {str(e)}")
            raise
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming message and perform search"""
        try:
            query = message.get('text', '')
            if not query:
                return {
                    'status': 'error',
                    'message': 'No search query provided'
                }
            
            try:
                results = await self.search(query)
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f"Error processing search: {str(e)}"
                }
            
            if not results:
                return {
                    'status': 'error',
                    'message': 'No results found'
                }
            
            # Format results for response
            response_text = "Search Results:\n\n"
            for i, result in enumerate(results, 1):
                response_text += f"{i}. {result['title']}\n"
                response_text += f"   {result['url']}\n"
                response_text += f"   {result['snippet']}\n\n"
            
            return {
                'status': 'success',
                'message': response_text
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error processing search: {str(e)}"
            } 
"""
Client Context Manager - Load and parse client protocols
"""
from pathlib import Path
from typing import Dict, Optional
import json

class ClientContext:
    """Manages client protocol data"""
    
    def __init__(self, client_id: str, protocols_dir: Path):
        self.client_id = client_id
        self.client_dir = protocols_dir / client_id
        self.protocol_path = self.client_dir / "protocol.json"
        self.metadata_path = self.client_dir / "metadata.json"
    
    def save_protocol(self, protocol_content, metadata: Optional[Dict] = None):
        """Save client protocol (dict or JSON string) and metadata"""
        self.client_dir.mkdir(parents=True, exist_ok=True)
        
        # Normalize to dict then save as JSON
        data = protocol_content if isinstance(protocol_content, dict) else json.loads(protocol_content)
        self.protocol_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        
        # Save metadata
        if metadata:
            self.metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    
    def load_protocol(self) -> dict:
        """Load client protocol as dict"""
        if not self.protocol_path.exists():
            raise FileNotFoundError(f"Protocol not found for client {self.client_id}")
        return json.loads(self.protocol_path.read_text(encoding='utf-8'))
    
    def load_metadata(self) -> Dict:
        """Load client metadata"""
        if not self.metadata_path.exists():
            return {}
        return json.loads(self.metadata_path.read_text(encoding='utf-8'))
    
    def exists(self) -> bool:
        """Check if client protocol exists"""
        return self.protocol_path.exists()

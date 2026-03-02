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
        self.protocol_path = self.client_dir / "protocol.md"
        self.metadata_path = self.client_dir / "metadata.json"
    
    def save_protocol(self, protocol_content: str, metadata: Optional[Dict] = None):
        """Save client protocol and metadata"""
        self.client_dir.mkdir(parents=True, exist_ok=True)
        
        # Save protocol
        self.protocol_path.write_text(protocol_content, encoding='utf-8')
        
        # Save metadata
        if metadata:
            self.metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    
    def load_protocol(self) -> str:
        """Load client protocol content"""
        if not self.protocol_path.exists():
            raise FileNotFoundError(f"Protocol not found for client {self.client_id}")
        return self.protocol_path.read_text(encoding='utf-8')
    
    def load_metadata(self) -> Dict:
        """Load client metadata"""
        if not self.metadata_path.exists():
            return {}
        return json.loads(self.metadata_path.read_text(encoding='utf-8'))
    
    def exists(self) -> bool:
        """Check if client protocol exists"""
        return self.protocol_path.exists()
    
    def parse_sections(self) -> Dict[str, str]:
        """Parse protocol into sections"""
        content = self.load_protocol()
        sections = {}
        current_section = "header"
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                # Start new section
                current_section = line.replace('## ', '').strip().lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections

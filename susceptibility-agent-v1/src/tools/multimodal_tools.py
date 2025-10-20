import os
import json
import tempfile
from typing import Any, Optional, Type, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pathlib import Path
import subprocess

from src.utils.logger import get_logger

logger = get_logger(__name__)

"""
Tools created for:
    - text-based (DocumentAnalysisTool): analyzes text documents, PDFs, and other written reports for threat intelligence.
    - audio-based (AudioTranscriptionTool): transcribes audio files (mp3, wav, m4a, etc.) into text for threat analysis.
            The parameter NUM_SPEAKERS has been set to 2, which is the common in military conversations.
    - radar-based (RadarSignalProcessor): processes radar detection data for naval EW analysis (NEW)
    - ew-based (EWSignalProcessor): processes electronic warfare signal data (NEW)

For image-based inputs, the LLM itself handles it.
"""


# ============================================================================
# INPUT SCHEMAS FOR PYDANTIC VALIDATION
# ============================================================================

class AudioTranscriptionInput(BaseModel):
    """Input schema for audio transcription."""
    audio_path: str = Field(
        ...,
        description="Path to the audio file to transcribe (mp3, wav, m4a, etc.)"
    )


class DocumentAnalysisInput(BaseModel):
    """Input schema for document analysis."""
    document_path: str = Field(
        ...,
        description="Path to the document file to analyze (txt, pdf)"
    )


class InputTypeDeterminerInput(BaseModel):
    """Input schema for input type determination."""
    input_data: str = Field(
        ...,
        description="File path or direct text content to analyze"
    )


class RadarSignalInput(BaseModel):
    """Input schema for radar signal processing."""
    signal_data: str = Field(
        ...,
        description="JSON string or file path containing radar detection data"
    )


class EWSignalInput(BaseModel):
    """Input schema for electronic warfare signal processing."""
    signal_data: str = Field(
        ...,
        description="JSON string or file path containing EW signal data"
    )


# ============================================================================
# AUDIO TRANSCRIPTION TOOL (PRESERVED FROM ORIGINAL)
# ============================================================================

class AudioTranscriptionTool(BaseTool):
    """Transcribes audio files into text with speaker diarization"""
    name: str = "Audio Transcription Tool"
    description: str = (
        "Transcribes audio files (mp3, wav, m4a, etc.) into text for threat analysis. "
        "Now includes speaker diarization using pyannote.audio. "
        "Input: audio_path (string - path to audio file)"
    )
    args_schema: Type[BaseModel] = AudioTranscriptionInput
    
    whisper_model: Optional[Any] = None
    diarization_pipeline: Optional[Any] = None

    def _load_whisper_model(self):
        """Lazy load whisper model only when needed"""
        if self.whisper_model is None:
            try:
                import whisper
                logger.info("Loading Whisper model...")
                self.whisper_model = whisper.load_model("base")
                logger.info("Whisper model loaded successfully")
            except ImportError:
                logger.error("Whisper not installed")
                raise ImportError(
                    "Whisper is not installed. Install it with: pip install openai-whisper"
                )
        return self.whisper_model

    def _load_diarization_pipeline(self):
        """Lazy load diarization pipeline only when needed"""
        if self.diarization_pipeline is None:
            try:
                from pyannote.audio import Pipeline
                hf_token = os.getenv("HF_TOKEN", None)
                
                if not hf_token:
                    logger.error("HF_TOKEN not found in environment")
                    raise ValueError(
                        "HF_TOKEN not found in environment. "
                        "Get your token from https://huggingface.co/settings/tokens"
                    )
                
                logger.info("Loading pyannote speaker-diarization model...")
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
                logger.info("Diarization model loaded successfully")

            except Exception as e:
                error_msg = str(e)
                if "gated" in error_msg.lower() or "private" in error_msg.lower():
                    logger.error("Authentication failed for pyannote model")
                    raise ValueError(
                        "Error accessing the pyannote model. Authentication failed for pyannote model'."
                    )

                logger.error(f"Pyannote dependencies not available: {e}")
                raise ImportError(
                    f"Pyannote.audio dependencies not available: {e}\n"
                    "This may be due to PyTorch compatibility issues on your system."
                )
        return self.diarization_pipeline
    
    def _run(self, audio_path: str) -> str:
        try:
            logger.info(f"Starting audio transcription for: {audio_path}")
            
            if not os.path.exists(audio_path):
                logger.error(f"Audio file not found: {audio_path}")
                return f"Error: Audio file not found at {audio_path}"

            # Step 1: Execute diarization
            try:
                diar_pipeline = self._load_diarization_pipeline()
                model = self._load_whisper_model()
            except (ImportError, RuntimeError, OSError) as e:
                logger.error(f"Audio transcription dependencies error: {e}")
                return (
                    f"ERROR: Audio transcription dependencies not available\n"
                    f"Details: {str(e)}\n\n"
                    f"WORKAROUND: Audio transcription requires:\n"
                    f"1. Working PyTorch installation\n"
                    f"2. pyannote.audio\n"
                    f"3. HuggingFace token (HF_TOKEN in .env)\n\n"
                )
            
            NUM_SPEAKERS = 2  # Force 2 speakers for military conversations
            logger.debug(f"Running diarization with {NUM_SPEAKERS} speakers")
            diarization = diar_pipeline(audio_path, num_speakers=NUM_SPEAKERS)

            # Step 2: Load Whisper model
            model = self._load_whisper_model()

            # Step 3: Create speaker-labeled text
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start, end = turn.start, turn.end
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_segment:
                    # Extract corresponding segment
                    subprocess.run([
                        "ffmpeg", "-y", "-i", audio_path,
                        "-ss", str(start), "-to", str(end),
                        "-ar", "16000", "-ac", "1", tmp_segment.name
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    result = model.transcribe(tmp_segment.name, language=None)
                    transcription = result["text"].strip()
                    if transcription:
                        segments.append(f"{speaker}: {transcription}")

            full_transcription = "\n".join(segments)
            logger.info(f"Transcription completed: {len(segments)} segments")

            formatted_output = f"""
            AUDIO TRANSCRIPTION REPORT:
            ==========================
            Speakers detected: {NUM_SPEAKERS}
            Transcription:
            {full_transcription}
            ==========================
            """
            return formatted_output.strip()

        except Exception as e:
            logger.error(f"Error processing audio file: {e}", exc_info=True)
            return f"Error processing audio file: {str(e)}"


# ============================================================================
# DOCUMENT ANALYSIS TOOL (PRESERVED FROM ORIGINAL)
# ============================================================================

class DocumentAnalysisTool(BaseTool):
    name: str = "Document Analysis Tool"
    description: str = (
        "Analyzes text documents, PDFs, and other written reports for threat intelligence. "
        "Input: document_path (string - path to document file)"
    )
    args_schema: Type[BaseModel] = DocumentAnalysisInput
    
    def _run(self, document_path: str) -> str:
        try:
            logger.info(f"Analyzing document: {document_path}")
            
            # Verify file exists
            if not os.path.exists(document_path):
                logger.error(f"Document not found: {document_path}")
                return f"Error: Document file not found at {document_path}"
            
            file_extension = Path(document_path).suffix.lower()
            
            if file_extension == '.txt':
                content = self._read_text_file(document_path)
            elif file_extension == '.pdf':
                content = self._read_pdf_file(document_path)
            else:
                logger.warning(f"Unsupported document type: {file_extension}")
                return f"Unsupported document type: {file_extension}"
            
            logger.info(f"Document analyzed successfully: {len(content)} characters")
            
            formatted_output = f"""
            DOCUMENT ANALYSIS REPORT:
            ========================
            File: {os.path.basename(document_path)}

            Content:
            {content}
            ========================
            """
            return formatted_output.strip()
            
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            return f"Error processing document: {str(e)}"
    
    def _read_text_file(self, file_path: str) -> str:
        """Read plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            return f"Error reading text file: {str(e)}"
    
    def _read_pdf_file(self, file_path: str) -> str:
        """Read PDF file using PyPDF2"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except ImportError:
            logger.error("PyPDF2 not installed")
            return "PDF processing requires PyPDF2: pip install PyPDF2"
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return f"Error reading PDF file: {str(e)}"


# ============================================================================
# INPUT TYPE DETERMINER TOOL (PRESERVED FROM ORIGINAL)
# ============================================================================

class InputTypeDeterminerTool(BaseTool):
    name: str = "Input Type Determiner"
    description: str = (
        "Determines the type of input (text, audio, image, document, radar, EW signal) and recommends which processing tool to use. "
        "Input: input_data (string - file path or direct text content)"
    )
    args_schema: Type[BaseModel] = InputTypeDeterminerInput
    
    def _run(self, input_data: str) -> str:
        logger.debug(f"Determining input type for: {input_data[:100]}...")
        
        # Check if it's a file path
        if os.path.exists(input_data):
            file_path = input_data
            file_extension = Path(file_path).suffix.lower()
            
            # Audio formats
            if file_extension in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
                logger.info(f"Detected audio file: {file_extension}")
                return f"""
                INPUT TYPE: AUDIO FILE
                Detected: {file_extension.upper()} audio file
                Recommendation: Use Audio Transcription Tool to convert to text
                File: {os.path.basename(file_path)}
                """
        
            # Document formats
            elif file_extension in ['.txt', '.pdf', '.doc', '.docx']:
                logger.info(f"Detected document file: {file_extension}")
                return f"""
                INPUT TYPE: DOCUMENT FILE
                Detected: {file_extension.upper()} document file
                Recommendation: Use Document Analysis Tool to process text content
                File: {os.path.basename(file_path)}
                """
            
            # JSON (could be radar/EW data)
            elif file_extension == '.json':
                logger.info("Detected JSON file - checking for signal data")
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if 'detections' in data or 'emitters' in data:
                            return f"""
                            INPUT TYPE: SIGNAL DATA (JSON)
                            Detected: Naval signal data in JSON format
                            Recommendation: Use Radar Signal Processor or EW Signal Processor
                            File: {os.path.basename(file_path)}
                            """
                except:
                    pass
                return f"""
                INPUT TYPE: JSON FILE
                Detected: Generic JSON data file
                Recommendation: Process as structured data
                File: {os.path.basename(file_path)}
                """
            
            # Image formats
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
                logger.info(f"Detected image file: {file_extension}")
                return f"""
                INPUT TYPE: IMAGE FILE
                Detected: {file_extension.upper()} image file
                Recommendation: Process this image yourself or use AddImageTool if available.
                Remember to look for visual threats in military context.
                File: {os.path.basename(file_path)}
                """
            
            # Unknown file type
            else:
                logger.warning(f"Unknown file type: {file_extension}")
                return f"""
                INPUT TYPE: UNKNOWN FILE
                Detected: {file_extension.upper()} file (unsupported format)
                Recommendation: Convert to supported format, provide text directly or directly analyze
                File: {os.path.basename(file_path)}
                """
        
        # Try to parse as JSON (signal data)
        try:
            data = json.loads(input_data)
            if isinstance(data, dict) and ('detections' in data or 'emitters' in data):
                logger.info("Detected inline signal data (JSON)")
                return """
                INPUT TYPE: SIGNAL DATA (INLINE JSON)
                Detected: Naval signal data as JSON string
                Recommendation: Use Radar Signal Processor or EW Signal Processor
                """
        except json.JSONDecodeError:
            pass
        
        # Assume it's direct text input
        word_count = len(input_data.split())
        logger.info(f"Detected direct text input: {word_count} words")
        return f"""
        INPUT TYPE: DIRECT TEXT
        Detected: Text input with {word_count} words
        Recommendation: Process directly for threat analysis
        No additional tools needed - ready for tactical assessment
        """


# ============================================================================
# NEW: RADAR SIGNAL PROCESSOR TOOL
# ============================================================================

class RadarSignalProcessor(BaseTool):
    """Processes radar detection data for naval electronic warfare analysis"""
    name: str = "Radar Signal Processor"
    description: str = (
        "Processes radar and ESM detection data to identify electromagnetic emitters. "
        "Extracts emitter characteristics including type, frequency, power, and bearing. "
        "Input: signal_data (JSON string or file path with radar detections)"
    )
    args_schema: Type[BaseModel] = RadarSignalInput
    
    def _run(self, signal_data: str) -> str:
        try:
            logger.info("Processing radar signal data")
            
            # Parse input (file or JSON string)
            data = self._parse_signal_data(signal_data)
            
            if not data:
                logger.error("Failed to parse signal data")
                return "ERROR: Could not parse radar signal data"
            
            # Extract detections
            detections = data.get('detections', [])
            if not detections:
                logger.warning("No detections found in signal data")
                return "NO DETECTIONS: No emitters detected in provided data"
            
            logger.info(f"Processing {len(detections)} detections")
            
            # Process each detection
            processed_detections = []
            for det in detections:
                processed = {
                    'emitter_id': det.get('emitter_id', 'UNKNOWN'),
                    'type': det.get('emitter_type', 'unknown'),
                    'frequency': f"{det.get('frequency_mhz', 0):.2f} MHz",
                    'power': f"{det.get('power_dbm', 0):.1f} dBm",
                    'bearing': f"{det.get('bearing_degrees', 0):.1f}°" if det.get('bearing_degrees') else "Unknown",
                    'range': f"{det.get('range_km', 0):.1f} km" if det.get('range_km') else "Unknown",
                    'classification': det.get('classification', 'Unclassified')
                }
                processed_detections.append(processed)
            
            # Build report
            report = self._build_radar_report(processed_detections, data)
            logger.info("Radar signal processing completed")
            
            return report
            
        except Exception as e:
            logger.error(f"Error processing radar signals: {e}", exc_info=True)
            return f"ERROR processing radar data: {str(e)}"
    
    def _parse_signal_data(self, signal_data: str) -> Optional[dict]:
        """Parse signal data from file or JSON string"""
        try:
            # Try as file path first
            if os.path.exists(signal_data):
                logger.debug(f"Reading signal data from file: {signal_data}")
                with open(signal_data, 'r') as f:
                    return json.load(f)
            
            # Try as JSON string
            logger.debug("Parsing signal data as JSON string")
            return json.loads(signal_data)
        
        except Exception as e:
            logger.error(f"Failed to parse signal data: {e}")
            return None
    
    def _build_radar_report(self, detections: List[dict], raw_data: dict) -> str:
        """Build formatted radar detection report"""
        
        sensor_type = raw_data.get('sensor_type', 'Unknown')
        mode = raw_data.get('operational_mode', 'normal')
        
        report_lines = [
            "=" * 70,
            "RADAR SIGNAL INTELLIGENCE REPORT",
            "=" * 70,
            f"Sensor Type: {sensor_type.upper()}",
            f"Operational Mode: {mode.upper()}",
            f"Total Detections: {len(detections)}",
            "",
            "DETECTED EMITTERS:",
            "-" * 70
        ]
        
        for det in detections:
            report_lines.extend([
                f"",
                f"Emitter ID: {det['emitter_id']}",
                f"  Type: {det['type']}",
                f"  Classification: {det['classification']}",
                f"  Frequency: {det['frequency']}",
                f"  Power: {det['power']}",
                f"  Bearing: {det['bearing']}",
                f"  Range: {det['range']}"
            ])
        
        report_lines.extend([
            "",
            "=" * 70,
            "SUMMARY: Radar detections processed and ready for threat assessment"
        ])
        
        return "\n".join(report_lines)


# ============================================================================
# NEW: EW SIGNAL PROCESSOR TOOL
# ============================================================================

class EWSignalProcessor(BaseTool):
    """Processes electronic warfare signal data including jamming and interference"""
    name: str = "EW Signal Processor"
    description: str = (
        "Processes electronic warfare signals including jamming, interference, and hostile emissions. "
        "Identifies threat sources and characterizes attack patterns. "
        "Input: signal_data (JSON string or file path with EW signal data)"
    )
    args_schema: Type[BaseModel] = EWSignalInput
    
    def _run(self, signal_data: str) -> str:
        try:
            logger.info("Processing EW signal data")
            
            # Parse input
            data = self._parse_signal_data(signal_data)
            
            if not data:
                logger.error("Failed to parse EW signal data")
                return "ERROR: Could not parse EW signal data"
            
            # Extract attack information
            attacks = data.get('attacks', [])
            jammers = data.get('jammers', [])
            
            if not attacks and not jammers:
                logger.warning("No EW threats detected")
                return "NO THREATS: No electronic warfare activity detected"
            
            logger.info(f"Processing {len(attacks)} attacks and {len(jammers)} jammers")
            
            # Build report
            report = self._build_ew_report(attacks, jammers, data)
            logger.info("EW signal processing completed")
            
            return report
            
        except Exception as e:
            logger.error(f"Error processing EW signals: {e}", exc_info=True)
            return f"ERROR processing EW data: {str(e)}"
    
    def _parse_signal_data(self, signal_data: str) -> Optional[dict]:
        """Parse EW signal data from file or JSON string"""
        try:
            if os.path.exists(signal_data):
                logger.debug(f"Reading EW data from file: {signal_data}")
                with open(signal_data, 'r') as f:
                    return json.load(f)
            
            logger.debug("Parsing EW data as JSON string")
            return json.loads(signal_data)
        
        except Exception as e:
            logger.error(f"Failed to parse EW data: {e}")
            return None
    
    def _build_ew_report(self, attacks: List[dict], jammers: List[dict], raw_data: dict) -> str:
        """Build formatted EW threat report"""
        
        report_lines = [
            "=" * 70,
            "ELECTRONIC WARFARE THREAT REPORT",
            "=" * 70,
            f"Total Attack Sources: {len(attacks)}",
            f"Total Jamming Sources: {len(jammers)}",
            ""
        ]
        
        if attacks:
            report_lines.extend([
                "ACTIVE ATTACKS:",
                "-" * 70
            ])
            for attack in attacks:
                report_lines.extend([
                    f"",
                    f"Attack ID: {attack.get('attack_id', 'UNKNOWN')}",
                    f"  Type: {attack.get('attack_type', 'Unknown')}",
                    f"  Target System: {attack.get('target_system', 'Unknown')}",
                    f"  Intensity: {attack.get('intensity', 'Unknown')}",
                    f"  Source Location: {attack.get('source_location', 'Unknown')}",
                    f"  Status: {attack.get('status', 'Active')}"
                ])
        
        if jammers:
            report_lines.extend([
                "",
                "JAMMING SOURCES:",
                "-" * 70
            ])
            for jammer in jammers:
                report_lines.extend([
                    f"",
                    f"Jammer ID: {jammer.get('jammer_id', 'UNKNOWN')}",
                    f"  Frequency Band: {jammer.get('frequency_band', 'Unknown')}",
                    f"  Power Level: {jammer.get('power_level', 'Unknown')}",
                    f"  Affected Systems: {', '.join(jammer.get('affected_systems', ['Unknown']))}",
                    f"  Bearing: {jammer.get('bearing_degrees', 'Unknown')}°"
                ])
        
        report_lines.extend([
            "",
            "=" * 70,
            "SUMMARY: EW threats identified and ready for countermeasure assessment"
        ])
        
        return "\n".join(report_lines)
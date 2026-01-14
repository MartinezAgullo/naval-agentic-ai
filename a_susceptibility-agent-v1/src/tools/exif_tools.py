import os
import subprocess
from typing import Optional, Dict, Any, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pathlib import Path

# Try to import exiftool wrapper
try:
    import exiftool
    EXIFTOOL_AVAILABLE = True
except ImportError:
    EXIFTOOL_AVAILABLE = False


class ExifExtractionInput(BaseModel):
    """Input schema for EXIF extraction."""
    file_path: str = Field(
        ...,
        description="Path to the image or media file to extract metadata from"
    )


class ExifMetadataExtractor(BaseTool):
    """Extracts EXIF metadata including GPS coordinates from images and media files"""
    name: str = "EXIF Metadata Extractor"
    description: str = (
        "Extracts EXIF metadata from images and audio/video files, including GPS coordinates, "
        "timestamp, and device information. Only reports available metadata. "
        "Particularly useful for geolocating media from the field. "
        "Input: file_path (string - path to image/audio/video file)"
    )
    args_schema: Type[BaseModel] = ExifExtractionInput
    
    def _run(self, file_path: str) -> str:
        """Extract EXIF metadata from file using exiftool."""
        try:
            if not os.path.exists(file_path):
                return f"Error: File not found at {file_path}"
            
            if not EXIFTOOL_AVAILABLE:
                return (
                    "ERROR: PyExifTool not installed\n"
                    "Install: uv pip install PyExifTool\n"
                    "System requirement: brew install exiftool (macOS) | "
                    "sudo apt-get install libimage-exiftool-perl (Linux)"
                )
            
            # Check if exiftool binary is actually installed
            if not self._check_exiftool_binary():
                return (
                    "ERROR: ExifTool binary not found\n"
                    "Install: brew install exiftool (macOS) | "
                    "sudo apt-get install libimage-exiftool-perl (Linux)\n"
                    "PyExifTool is installed but needs the exiftool command-line tool."
                )
            
            # Extract metadata using PyExifTool with coordinate format
            metadata = self._extract_metadata(file_path)
            
            if not metadata or len(metadata) == 0:
                return f"NO_METADATA: No extractable metadata found in {os.path.basename(file_path)}"
            
            # Build concise report with only available data
            formatted_output = self._format_metadata_report(metadata, file_path)
            
            return formatted_output
            
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _check_exiftool_binary(self) -> bool:
        """Check if exiftool command-line tool is actually installed"""
        try:
            result = subprocess.run(
                ['exiftool', '-ver'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _extract_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata using PyExifTool with decimal GPS coordinates"""
        try:
            with exiftool.ExifToolHelper() as et:
                # Use -n flag to get GPS coordinates in decimal format
                # Use -G flag to get group names
                metadata_list = et.get_metadata([file_path])
                
                if metadata_list and len(metadata_list) > 0:
                    metadata = metadata_list[0]
                    
                    # Filter out only system paths and tool version
                    filtered_metadata = {
                        k: v for k, v in metadata.items()
                        if not k.startswith(('SourceFile', 'ExifTool:ExifToolVersion'))
                        and k not in ['Directory', 'FileName']  # Keep other File: fields
                        and v not in [None, '']
                    }
                    
                    return filtered_metadata if filtered_metadata else None        
            return None
        
        except Exception as e:
            print(f"Error running exiftool: {e}")
            return None
    
    def _format_metadata_report(self, metadata: Dict[str, Any], file_path: str) -> str:
        """Format metadata into a concise tactical intelligence report - only available fields"""
        
        report_lines = [
            "=" * 70,
            "METADATA INTELLIGENCE REPORT",
            "=" * 70,
            f"File: {os.path.basename(file_path)}",
        ]
        
        # File type
        file_type = self._get_field(metadata, 'FileType', 'MIMEType')
        if file_type:
            if '/' in str(file_type):
                file_type = str(file_type).split('/')[-1].upper()
            report_lines.append(f"Type: {file_type}")
        
        report_lines.append("")
        
        # GPS LOCATION (Highest Priority)
        gps_data = self._extract_gps_info(metadata)
        if gps_data:
            report_lines.extend([
                "🎯 GPS LOCATION (PRIORITY INTELLIGENCE)",
                "-" * 70,
                f"Coordinates: {gps_data['coordinates']}",
                f"Latitude:    {gps_data['latitude']}",
                f"Longitude:   {gps_data['longitude']}",
            ])
            
            if gps_data.get('altitude'):
                report_lines.append(f"Altitude:    {gps_data['altitude']}")
            
            report_lines.extend([
                "",
                "⚠️  Use these GPS coordinates to override manual location input",
                ""
            ])
        
        # TIMESTAMP
        timestamp_data = self._extract_timestamp_info(metadata)
        if timestamp_data:
            report_lines.append("TIMESTAMP")
            report_lines.append("-" * 70)
            
            if timestamp_data.get('datetime_original'):
                report_lines.append(f"Date/Time: {timestamp_data['datetime_original']}")
            
            if timestamp_data.get('timezone'):
                report_lines.append(f"Timezone:  {timestamp_data['timezone']}")
            
            report_lines.append("")
        
        # DEVICE/CAMERA INFORMATION
        device_data = self._extract_device_info(metadata)
        if device_data:
            report_lines.append("DEVICE/CAMERA")
            report_lines.append("-" * 70)
            
            if device_data.get('make'):
                report_lines.append(f"Make:  {device_data['make']}")
            
            if device_data.get('model'):
                report_lines.append(f"Model: {device_data['model']}")
            
            if device_data.get('serial'):
                report_lines.append(f"Serial: {device_data['serial']}")
            
            if device_data.get('owner'):
                report_lines.append(f"Owner: {device_data['owner']}")
            
            if device_data.get('software'):
                report_lines.append(f"Software: {device_data['software']}")
            
            report_lines.append("")
        
        # AUDIO-SPECIFIC METADATA
        audio_data = self._extract_audio_info(metadata)
        if audio_data:
            report_lines.append("AUDIO PROPERTIES")
            report_lines.append("-" * 70)
            
            if audio_data.get('duration'):
                report_lines.append(f"Duration: {audio_data['duration']}")
            
            if audio_data.get('sample_rate'):
                report_lines.append(f"Sample Rate: {audio_data['sample_rate']}")
            
            if audio_data.get('channels'):
                report_lines.append(f"Channels: {audio_data['channels']}")
            
            if audio_data.get('bitrate'):
                report_lines.append(f"Bitrate: {audio_data['bitrate']}")
            
            report_lines.append("")
        
        # IMAGE-SPECIFIC METADATA
        image_data = self._extract_image_info(metadata)
        if image_data:
            report_lines.append("IMAGE PROPERTIES")
            report_lines.append("-" * 70)
            
            if image_data.get('dimensions'):
                report_lines.append(f"Dimensions: {image_data['dimensions']}")
            
            if image_data.get('megapixels'):
                report_lines.append(f"Megapixels: {image_data['megapixels']}")
            
            if image_data.get('color_type'):
                report_lines.append(f"Color Type: {image_data['color_type']}")
            
            if image_data.get('bit_depth'):
                report_lines.append(f"Bit Depth: {image_data['bit_depth']}")
            
            report_lines.append("")
        
        # FILE SIZE
        file_size = self._get_field(metadata, 'FileSize')
        if file_size:
            report_lines.append(f"File Size: {file_size}")
            report_lines.append("")
        
        # INTELLIGENCE SUMMARY
        summary_items = []
        
        if gps_data:
            summary_items.append("✅ GPS coordinates available - HIGH confidence geolocation")
        else:
            summary_items.append("⚠️  NO GPS DATA - Use fallback location methods")
        
        if timestamp_data:
            summary_items.append("✅ Timestamp available for temporal analysis")
        
        if device_data:
            device_parts = []
            if device_data.get('make'):
                device_parts.append(device_data['make'])
            if device_data.get('model'):
                device_parts.append(device_data['model'])
            if device_parts:
                summary_items.append(f"📱 Source device: {' '.join(device_parts)}")
            if device_data.get('owner'):
                summary_items.append(f"👤 Owner: {device_data['owner']}")
        
        if audio_data and audio_data.get('duration'):
            summary_items.append(f"🎵 Audio recording: {audio_data['duration']}")
        
        if summary_items:
            report_lines.append("INTELLIGENCE SUMMARY")
            report_lines.append("-" * 70)
            report_lines.extend(summary_items)
            report_lines.append("")
        
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)
    
    def _get_field(self, metadata: Dict[str, Any], *keys: str) -> Optional[Any]:
        """Helper to get field from metadata with multiple possible key formats"""
        for key in keys:
            # Try direct key
            if key in metadata:
                value = metadata[key]
                if value not in [None, '', 'undef']:
                    return value
            
            # Try without namespace prefix if key has one
            if ':' in key:
                simple_key = key.split(':')[-1]
                if simple_key in metadata:
                    value = metadata[simple_key]
                    if value not in [None, '', 'undef']:
                        return value
            
            # Try adding common namespace prefixes
            for prefix in ['EXIF:', 'GPS:', 'XMP:', 'IPTC:', 'Composite:', 'File:', 'PNG:', 'JFIF:', 'IFD0:']:
                full_key = f"{prefix}{key}"
                if full_key in metadata:
                    value = metadata[full_key]
                    if value not in [None, '', 'undef']:
                        return value
        
        return None
    
    def _extract_gps_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract GPS information - handles both decimal and DMS formats"""
        
        # Try to get GPS position (this is already in a good format from ExifTool)
        gps_pos = self._get_field(metadata, 'GPSPosition')
        lat = self._get_field(metadata, 'GPSLatitude')
        lon = self._get_field(metadata, 'GPSLongitude')
        
        # If we have the composite GPSPosition, parse it
        if gps_pos and isinstance(gps_pos, str):
            # Format: "36 deg 51' 36.83" N, 2 deg 33' 28.47" W"
            # Use the raw lat/lon values if available (they're already formatted)
            if lat and lon:
                gps_info = {
                    'latitude': str(lat),
                    'longitude': str(lon),
                    'coordinates': f"{lat}, {lon}"
                }
            else:
                # Fallback: use GPSPosition as-is
                gps_info = {
                    'latitude': gps_pos.split(',')[0].strip() if ',' in gps_pos else gps_pos,
                    'longitude': gps_pos.split(',')[1].strip() if ',' in gps_pos else '',
                    'coordinates': gps_pos
                }
        elif lat and lon:
            gps_info = {
                'latitude': str(lat),
                'longitude': str(lon),
                'coordinates': f"{lat}, {lon}"
            }
        else:
            return None
        
        # Add altitude if available
        alt = self._get_field(metadata, 'GPSAltitude', 'Altitude')
        alt_ref = self._get_field(metadata, 'GPSAltitudeRef')
        if alt:
            alt_str = str(alt)
            if alt_ref:
                alt_str += f" ({alt_ref})"
            gps_info['altitude'] = alt_str
        
        return gps_info
    
    def _extract_timestamp_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract timestamp information"""
        
        dt_original = self._get_field(metadata, 'DateTimeOriginal', 'CreateDate', 
                                     'DateTime', 'FileModifyDate', 'ModifyDate')
        
        if not dt_original:
            return None
        
        timestamp_info = {
            'datetime_original': str(dt_original)
        }
        
        # Add timezone if available
        timezone = self._get_field(metadata, 'OffsetTime', 'TimeZone')
        if timezone:
            timestamp_info['timezone'] = str(timezone)
        
        return timestamp_info
    
    def _extract_device_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract device/camera information including custom fields"""
        
        make = self._get_field(metadata, 'Make')
        model = self._get_field(metadata, 'Model')
        serial = self._get_field(metadata, 'SerialNumber')
        owner = self._get_field(metadata, 'OwnerName', 'Owner', 'Artist')
        software = self._get_field(metadata, 'Software')
        
        if not (make or model or serial or owner or software):
            return None
        
        device_info = {}
        
        if make:
            device_info['make'] = str(make).strip()
        if model:
            device_info['model'] = str(model).strip()
        if serial:
            device_info['serial'] = str(serial).strip()
        if owner:
            device_info['owner'] = str(owner).strip()
        if software:
            device_info['software'] = str(software).strip()
        
        return device_info
    
    def _extract_audio_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract audio-specific information"""
        
        duration = self._get_field(metadata, 'Duration')
        sample_rate = self._get_field(metadata, 'SampleRate', 'AudioSampleRate')
        channels = self._get_field(metadata, 'Channels', 'AudioChannels')
        bitrate = self._get_field(metadata, 'AudioBitrate', 'Bitrate')
        
        if not (duration or sample_rate or channels or bitrate):
            return None
        
        audio_info = {}
        
        if duration:
            audio_info['duration'] = str(duration)
        if sample_rate:
            audio_info['sample_rate'] = str(sample_rate)
        if channels:
            audio_info['channels'] = str(channels)
        if bitrate:
            audio_info['bitrate'] = str(bitrate)
        
        return audio_info
    
    def _extract_image_info(self, metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract image-specific information"""
        
        width = self._get_field(metadata, 'ImageWidth')
        height = self._get_field(metadata, 'ImageHeight')
        megapixels = self._get_field(metadata, 'Megapixels')
        color_type = self._get_field(metadata, 'ColorType')
        bit_depth = self._get_field(metadata, 'BitDepth')
        
        if not (width or height or megapixels or color_type or bit_depth):
            return None
        
        image_info = {}
        
        if width and height:
            image_info['dimensions'] = f"{width} x {height}"
        
        if megapixels:
            image_info['megapixels'] = str(megapixels)
        
        if color_type:
            image_info['color_type'] = str(color_type)
        
        if bit_depth:
            image_info['bit_depth'] = str(bit_depth)
        
        return image_info


# GPS-only tool remains the same
class GpsFromExifInput(BaseModel):
    """Input schema for extracting just GPS coordinates."""
    file_path: str = Field(
        ...,
        description="Path to the media file to extract GPS coordinates from"
    )


class GPSFromExifTool(BaseTool):
    """Quick tool to extract only GPS coordinates from media file EXIF data"""
    name: str = "GPS From EXIF Tool"
    description: str = (
        "Quickly extracts ONLY GPS coordinates from image or audio file EXIF data. "
        "Returns coordinates in format or 'NO_GPS' if not available. "
        "Use this for fast GPS extraction when you only need location data. "
        "Input: file_path (string - path to media file)"
    )
    args_schema: Type[BaseModel] = GpsFromExifInput
    
    def _run(self, file_path: str) -> str:
        """Extract only GPS coordinates from EXIF data"""
        try:
            if not os.path.exists(file_path):
                return "ERROR: File not found"
            
            if not EXIFTOOL_AVAILABLE:
                return "ERROR: PyExifTool not installed"
            
            with exiftool.ExifToolHelper() as et:
                metadata_list = et.get_metadata([file_path])
                if metadata_list and len(metadata_list) > 0:
                    metadata = metadata_list[0]
                    
                    # Get GPS position
                    gps_pos = metadata.get('GPSPosition')
                    lat = metadata.get('GPSLatitude')
                    lon = metadata.get('GPSLongitude')
                    
                    if lat and lon:
                        return f"{lat}, {lon}"
                    elif gps_pos:
                        return str(gps_pos)
            
            return "NO_GPS"
            
        except Exception as e:
            return f"ERROR: {str(e)}"
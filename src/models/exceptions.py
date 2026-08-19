"""
Custom exceptions for Quiz Shuffler structure validation.
"""

class QuizShufflerStructureError(Exception):
    """Base exception for all Quiz Shuffler structural errors."""
    pass

class MissingStartMarkerError(QuizShufflerStructureError):
    """Raised when <end 1> is found without preceding <type 1>."""
    def __init__(self, message: str = "Found '<end 1>' marker without preceding '<type 1>' marker."):
        super().__init__(message)

class MissingEndMarkerError(QuizShufflerStructureError):
    """Raised when <type 1> is found without matching <end 1>."""
    def __init__(self, message: str = "Found '<type 1>' marker without matching '<end 1>' marker."):
        super().__init__(message)

class InvalidClusterMarkerError(QuizShufflerStructureError):
    """Raised when an unrecognized cluster marker syntax is detected."""
    def __init__(self, marker: str):
        self.marker = marker
        super().__init__(f"Invalid cluster marker syntax detected: '{marker}'.")

class EmptyClusterError(QuizShufflerStructureError):
    """Raised when a cluster marker contains no question blocks."""
    def __init__(self, marker_type: str = ""):
        self.marker_type = marker_type
        msg = f"Cluster defined by '{marker_type}' contains no questions." if marker_type else "Cluster contains no questions."
        super().__init__(msg)

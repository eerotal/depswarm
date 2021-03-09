"""Generic exceptions for various cases."""


class UnsupportedVersionException(Exception):
    """Exception for indicating an unsupported version."""


class MissingDependencyException(Exception):
    """Exception for indicating a missing dependency."""

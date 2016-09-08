from django.utils.module_loading import import_string


def create_logger(logger_path, logger_corba_object, corba_ccreg):
    """
    Returns logger instance or None when logger_path is not set.

    @param logger_path: Path to the logger module.
    @param logger_corba_object: Corba object of Logger.
    @param corba_ccreg: Corba object ccReg.
    @raise ImportError: If logger_path is invalid.
    """
    logger_class = import_string(logger_path)
    return logger_class(logger_corba_object, corba_ccreg)

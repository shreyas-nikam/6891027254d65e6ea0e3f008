import pytest
import os
import pickle
from pathlib import Path
from definition_4e55e21928ba494b91f80008b98058d0 import save_model_artifact

# Test 1: Successful serialization and saving of a typical model object (dictionary)
def test_save_model_artifact_success_dict(tmp_path):
    """
    Test that a dictionary model object is successfully serialized and saved
    to a pickle file, and its content can be correctly loaded back.
    """
    model_obj = {"name": "IRRBB Model", "version": "1.0", "parameters": {"shock": 200}}
    file_path = tmp_path / "irrbb_gap_eve_model.pkl"
    
    save_model_artifact(model_obj, str(file_path))
    
    assert file_path.is_file()
    assert file_path.stat().st_size > 0  # Check if file is not empty
    
    with open(file_path, 'rb') as f:
        loaded_obj = pickle.load(f)
        
    assert loaded_obj == model_obj

# Test 2: Successful serialization and saving of a simple model object (e.g., None)
def test_save_model_artifact_success_none_object(tmp_path):
    """
    Test that None as a model object can be successfully serialized and saved.
    """
    model_obj = None
    file_path = tmp_path / "none_model_artifact.pkl"
    
    save_model_artifact(model_obj, str(file_path))
    
    assert file_path.is_file()
    assert file_path.stat().st_size > 0 # None can be pickled, resulting in a small file
    
    with open(file_path, 'rb') as f:
        loaded_obj = pickle.load(f)
        
    assert loaded_obj is None

# Test 3: Handling of invalid filename types
@pytest.mark.parametrize("invalid_filename", [
    123,           # Integer
    None,          # NoneType
    True,          # Boolean
    ["path", "to", "file.pkl"], # List
    Path("another/path/file.pkl") # Path object, should be converted to str
])
def test_save_model_artifact_invalid_filename_type(invalid_filename):
    """
    Test that a TypeError is raised when the provided filename is not a string.
    """
    model_obj = {"dummy": "data"}
    
    with pytest.raises(TypeError):
        save_model_artifact(model_obj, invalid_filename)

# Test 4: Handling of non-pickleable objects
def test_save_model_artifact_non_pickleable_object(tmp_path):
    """
    Test that a pickle.PicklingError is raised when the model_object cannot be serialized.
    A lambda function is a common example of a non-pickleable object.
    """
    # A lambda function cannot be pickled
    model_obj = lambda x: x * 2 
    file_path = tmp_path / "non_pickleable_artifact.pkl"
    
    with pytest.raises(pickle.PicklingError):
        save_model_artifact(model_obj, str(file_path))

# Test 5: Handling of file system errors (e.g., permission denied, non-existent directory)
def test_save_model_artifact_file_system_error(mocker):
    """
    Test that an OSError (or a subclass like PermissionError) is raised when
    there's an underlying issue with file writing due to OS permissions or
    an invalid directory path that cannot be created. This is simulated by
    mocking the built-in 'open' function to raise an error.
    """
    model_obj = {"config": {"base_path": "/data"}}
    # The actual filename string doesn't matter much here, as 'open' is mocked.
    # It just needs to be a string.
    filename = "/non/existent/or/restricted/path/simulation.pkl" 
    
    # Mock 'builtins.open' to raise an OSError when called for writing ('wb')
    mocker.patch("builtins.open", side_effect=OSError("Simulated file write error: Permission denied"))
    
    with pytest.raises(OSError):
        save_model_artifact(model_obj, filename)
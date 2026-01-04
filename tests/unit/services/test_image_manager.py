from src.services.image_manager import ImageManager


def test_process_upload(mocker):
    # 1. Arrange: Setup mocks for the external services
    # We patch the classes that ImageManager depends on
    mock_storage_class = mocker.patch("src.services.image_manager.StorageService")
    mock_metadata_class = mocker.patch("src.services.image_manager.MetadataService")

    # Create instances of the mocked services
    mock_storage_inst = mock_storage_class.return_value
    mock_metadata_inst = mock_metadata_class.return_value

    # Configure mock return values if necessary
    mock_storage_inst.upload_image.return_value = "s3.amazonaws.com"
    mock_metadata_inst.save_metadata.return_value = True

    # Initialize the manager with mocked dependencies
    manager = ImageManager()

    test_file_data = b"fake-image-content"
    test_filename = "test_image.jpg"

    # 2. Act: Call the orchestration method
    result = manager.process_upload(test_file_data, test_filename)

    # 3. Assert: Verify the manager interacted with both services correctly
    # Check if StorageService.upload was called with the correct data
    mock_storage_inst.upload_image.assert_called_once_with(test_file_data, test_filename)

    # Check if MetadataService.save was called (likely with the URL from storage)
    mock_metadata_inst.save_metadatas.assert_called_once()

    # Optional: Verify the final result
    assert result is True

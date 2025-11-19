import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="dxunjx7wa",
    api_key="183271731539698",
    api_secret="WjhFhczJET7-wAWu1fUs35PQW88"
)

result = cloudinary.uploader.upload(r"C:\tutoring_platform\static\images\review1.jpeg")
print(result)

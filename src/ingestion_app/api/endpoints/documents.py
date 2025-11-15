from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile
from pathlib import Path

from ..services.document_ingestion import document_ingestion_service
from ...app.utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["document_management"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("policy")
):
    """Upload and ingest a single document"""
    try:
        # Validate file type
        file_extension = Path(file.filename).suffix.lower()
        allowed_extensions = [".pdf", ".docx", ".txt"]
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Ingest the document
            result = await document_ingestion_service.ingest_document(
                temp_file_path, document_type
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if result["status"] == "success":
                logger.info(f"Document uploaded and ingested successfully: {file.filename}")
                return JSONResponse(
                    status_code=status.HTTP_201_CREATED,
                    content=result
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document ingestion failed: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            # Clean up temp file if it still exists
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/upload-multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    document_type: str = Form("policy")
):
    """Upload and ingest multiple documents"""
    try:
        results = []
        
        for file in files:
            try:
                # Validate file type
                file_extension = Path(file.filename).suffix.lower()
                allowed_extensions = [".pdf", ".docx", ".txt"]
                
                if file_extension not in allowed_extensions:
                    results.append({
                        "file_name": file.filename,
                        "status": "failed",
                        "error": f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
                    })
                    continue
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                # Ingest the document
                result = await document_ingestion_service.ingest_document(
                    temp_file_path, document_type
                )
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    "file_name": file.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Summary
        successful = len([r for r in results if r.get("status") == "success"])
        failed = len(results) - successful
        
        logger.info(f"Multiple document upload completed: {successful} successful, {failed} failed")
        
        return {
            "total_files": len(files),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Multiple document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multiple upload failed: {str(e)}"
        )

@router.post("/ingest-directory")
async def ingest_directory(
    directory_path: str = Form(...),
    document_type: str = Form("policy")
):
    """Ingest all documents from a directory path"""
    try:
        if not os.path.exists(directory_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {directory_path}"
            )
        
        results = await document_ingestion_service.ingest_directory(
            directory_path, document_type
        )
        
        # Summary
        successful = len([r for r in results if r.get("status") == "success"])
        failed = len(results) - successful
        
        return {
            "directory_path": directory_path,
            "total_files": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Directory ingestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Directory ingestion failed: {str(e)}"
        )

@router.get("/list")
async def list_documents():
    """List all documents in the vector database"""
    try:
        documents_info = document_ingestion_service.list_documents()
        return documents_info
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.delete("/document/{file_name}")
async def delete_document(file_name: str):
    """Delete a document and all its chunks from the vector database"""
    try:
        result = document_ingestion_service.delete_document(file_name)
        
        if result["status"] == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        elif result["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/health")
async def ingestion_health():
    """Health check for the document ingestion service"""
    try:
        import chromadb
        from pathlib import Path
        
        PROJECT_ROOT = Path(__file__).parents[4]
        client = chromadb.PersistentClient(
            path=str(PROJECT_ROOT / "data" / "chromadb")
        )
        collection = client.get_collection(name="banking_documents")
        collection_count = collection.count()
        
        return {
            "status": "healthy",
            "chromadb_status": "healthy",
            "total_documents": collection_count,
            "collection_name": "banking_documents",
            "can_query": True
        }
    except Exception as e:
        logger.error(f"Ingestion health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

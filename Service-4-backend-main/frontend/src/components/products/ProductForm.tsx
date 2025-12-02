import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { mockApiService as apiService } from '../../services/mockApi';

interface ProductFormData {
  name: string;
  description: string;
  price: number;
  stock_quantity: number;
  image_url: string;
}

const ProductForm: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [formData, setFormData] = useState<ProductFormData>({
    name: '',
    description: '',
    price: 0,
    stock_quantity: 0,
    image_url: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>('');

  // Load product data if editing
  useEffect(() => {
    if (isEditing && id) {
      loadProduct();
    }
  }, [isEditing, id]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      const product = await apiService.getProduct(parseInt(id!));
      setFormData({
        name: product.name,
        description: product.description || '',
        price: product.price,
        stock_quantity: product.stock_quantity || 0,
        image_url: product.image_url || ''
      });
      if (product.image_url) {
        setImagePreview(product.image_url);
      }
    } catch (error: any) {
      setError(error.message || 'Failed to load product');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : 
              type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadImage = async (): Promise<string> => {
    if (!imageFile) return formData.image_url;

    try {
      const result = await apiService.uploadImage(imageFile);
      return result.image_url;
    } catch (error: any) {
      throw new Error(`Failed to upload image: ${error.message}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Upload image if selected
      let imageUrl = formData.image_url;
      if (imageFile) {
        imageUrl = await uploadImage();
      }

      const productData = {
        ...formData,
        image_url: imageUrl
      };

      if (isEditing) {
        await apiService.updateProduct(parseInt(id!), productData);
      } else {
        await apiService.createProduct(productData);
      }
      
      navigate('/products');
    } catch (error: any) {
      setError(error.message || 'Failed to save product');
    } finally {
      setLoading(false);
    }
  };



  if (loading && isEditing) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="h3 mb-0">
          <i className="fas fa-plus me-2"></i>
          {isEditing ? 'Edit Product' : 'Add New Product'}
        </h1>
        <Link to="/products" className="btn btn-outline-secondary">
          <i className="fas fa-arrow-left me-1"></i>Back to Products
        </Link>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      
             <div className="card">
         <div className="card-body">
           <form onSubmit={handleSubmit}>
             <div className="row">
               {/* Basic Information */}
               <div className="col-md-6">
                 <div className="mb-3">
                   <label htmlFor="name" className="form-label">Product Name *</label>
                   <input
                     type="text"
                     className="form-control"
                     id="name"
                     name="name"
                     value={formData.name}
                     onChange={handleChange}
                     required
                     placeholder="Enter product name"
                   />
                 </div>

                 <div className="mb-3">
                   <label htmlFor="description" className="form-label">Description</label>
                   <textarea
                     className="form-control"
                     id="description"
                     name="description"
                     value={formData.description}
                     onChange={handleChange}
                     rows={3}
                     placeholder="Enter product description"
                   />
                 </div>

                 <div className="mb-3">
                   <label htmlFor="price" className="form-label">Price (₹) *</label>
                   <input
                     type="number"
                     className="form-control"
                     id="price"
                     name="price"
                     value={formData.price}
                     onChange={handleChange}
                     required
                     min="0"
                     step="0.01"
                     placeholder="0.00"
                   />
                 </div>

                 <div className="mb-3">
                   <label htmlFor="stock_quantity" className="form-label">Stock Quantity *</label>
                   <input
                     type="number"
                     className="form-control"
                     id="stock_quantity"
                     name="stock_quantity"
                     value={formData.stock_quantity}
                     onChange={handleChange}
                     required
                     min="0"
                     placeholder="0"
                   />
                   <div className="form-text">
                     Number of items available in stock
                   </div>
                 </div>
               </div>

               {/* Image Upload */}
               <div className="col-md-6">
                 <div className="mb-3">
                   <label htmlFor="image" className="form-label">Product Image</label>
                   <input
                     type="file"
                     className="form-control"
                     id="image"
                     accept="image/*"
                     onChange={handleImageChange}
                   />
                   <div className="form-text">
                     Supported formats: JPG, PNG, GIF. Max size: 5MB
                   </div>
                 </div>

                 {imagePreview && (
                   <div className="mb-3">
                     <label className="form-label">Image Preview</label>
                     <div>
                       <img
                         src={imagePreview}
                         alt="Product preview"
                         className="img-thumbnail"
                         style={{ maxWidth: '200px', maxHeight: '200px' }}
                       />
                     </div>
                   </div>
                 )}
               </div>
             </div>

            {/* Action Buttons */}
            <div className="d-flex justify-content-end gap-2 mt-4">
              <Link to="/products" className="btn btn-outline-secondary">
                Cancel
              </Link>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Saving...
                  </>
                ) : (
                  <>
                    <i className="fas fa-save me-2"></i>
                    {isEditing ? 'Update Product' : 'Create Product'}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProductForm;

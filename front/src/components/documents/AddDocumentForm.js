import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Input from '../common/Input';
import Button from '../common/Button';
import { addDocument } from '../../services/documentService';
import './AddDocumentForm.css';

/**
 * 添加文档表单组件
 */
const AddDocumentForm = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    source: '',
    metadata: {}
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [metadataFields, setMetadataFields] = useState([{ key: '', value: '' }]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
    
    // 清除错误
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: ''
      }));
    }
  };
  
  const handleMetadataChange = (index, field, value) => {
    const updatedFields = [...metadataFields];
    updatedFields[index][field] = value;
    setMetadataFields(updatedFields);
    
    // 更新 formData 中的 metadata
    const metadata = {};
    updatedFields.forEach((item) => {
      if (item.key && item.value) {
        metadata[item.key] = item.value;
      }
    });
    
    setFormData((prev) => ({
      ...prev,
      metadata
    }));
  };
  
  const addMetadataField = () => {
    setMetadataFields([...metadataFields, { key: '', value: '' }]);
  };
  
  const removeMetadataField = (index) => {
    const updatedFields = [...metadataFields];
    updatedFields.splice(index, 1);
    setMetadataFields(updatedFields);
    
    // 更新 formData 中的 metadata
    const metadata = {};
    updatedFields.forEach((item) => {
      if (item.key && item.value) {
        metadata[item.key] = item.value;
      }
    });
    
    setFormData((prev) => ({
      ...prev,
      metadata
    }));
  };
  
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.title.trim()) {
      newErrors.title = '请输入文档标题';
    }
    
    if (!formData.content.trim()) {
      newErrors.content = '请输入文档内容';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      setLoading(true);
      
      // 添加文档
      await addDocument(formData);
      
      // 成功后跳转到文档列表页
      navigate('/documents', { state: { success: '文档添加成功' } });
    } catch (error) {
      console.error('添加文档失败:', error);
      setErrors({
        submit: '添加文档失败，请稍后重试'
      });
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="add-document-form">
      <h2>添加新文档</h2>
      
      <form onSubmit={handleSubmit}>
        <Input
          label="标题"
          name="title"
          value={formData.title}
          onChange={handleChange}
          placeholder="输入文档标题"
          error={errors.title}
          required
        />
        
        <div className="form-group">
          <label htmlFor="content" className="form-label">
            内容 <span className="required-mark">*</span>
          </label>
          <textarea
            id="content"
            name="content"
            value={formData.content}
            onChange={handleChange}
            placeholder="输入文档内容"
            className={`form-textarea ${errors.content ? 'has-error' : ''}`}
            rows="10"
            required
          ></textarea>
          {errors.content && <div className="form-error">{errors.content}</div>}
        </div>
        
        <Input
          label="来源"
          name="source"
          value={formData.source}
          onChange={handleChange}
          placeholder="输入文档来源"
        />
        
        <div className="form-group">
          <label className="form-label">元数据</label>
          
          {metadataFields.map((field, index) => (
            <div key={index} className="metadata-field">
              <Input
                placeholder="键"
                value={field.key}
                onChange={(e) => handleMetadataChange(index, 'key', e.target.value)}
              />
              <Input
                placeholder="值"
                value={field.value}
                onChange={(e) => handleMetadataChange(index, 'value', e.target.value)}
              />
              <button
                type="button"
                className="remove-metadata-button"
                onClick={() => removeMetadataField(index)}
              >
                删除
              </button>
            </div>
          ))}
          
          <button
            type="button"
            className="add-metadata-button"
            onClick={addMetadataField}
          >
            添加元数据
          </button>
        </div>
        
        {errors.submit && <div className="form-error submit-error">{errors.submit}</div>}
        
        <div className="form-actions">
          <Button type="secondary" onClick={() => navigate('/documents')}>
            取消
          </Button>
          <Button type="primary" loading={loading}>
            添加文档
          </Button>
        </div>
      </form>
    </div>
  );
};

export default AddDocumentForm;
import React, { useState } from 'react';
import Button from '../common/Button';
import './SearchBar.css';

/**
 * 搜索栏组件
 * @param {Object} props - 组件属性
 * @param {Function} props.onSearch - 搜索回调函数
 * @param {string} [props.initialQuery=''] - 初始查询
 */
const SearchBar = ({ onSearch, initialQuery = '' }) => {
  const [query, setQuery] = useState(initialQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    source: '',
    dateFrom: '',
    dateTo: ''
  });
  
  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };
  
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // 构建元数据过滤条件
    const metadataFilter = {};
    
    if (filters.source) {
      metadataFilter.source = filters.source;
    }
    
    // 日期过滤
    if (filters.dateFrom || filters.dateTo) {
      metadataFilter.date = {};
      
      if (filters.dateFrom) {
        metadataFilter.date.from = filters.dateFrom;
      }
      
      if (filters.dateTo) {
        metadataFilter.date.to = filters.dateTo;
      }
    }
    
    onSearch({
      query,
      metadata_filter: Object.keys(metadataFilter).length > 0 ? metadataFilter : undefined
    });
  };
  
  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };
  
  const clearFilters = () => {
    setFilters({
      source: '',
      dateFrom: '',
      dateTo: ''
    });
  };
  
  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit}>
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={handleQueryChange}
            placeholder="搜索知识库..."
            className="search-input"
          />
          <Button type="primary">搜索</Button>
        </div>
        
        <div className="search-options">
          <button
            type="button"
            className="filter-toggle"
            onClick={toggleFilters}
          >
            {showFilters ? '隐藏过滤选项' : '显示过滤选项'}
          </button>
          
          {showFilters && (
            <div className="search-filters">
              <div className="filter-group">
                <label htmlFor="source" className="filter-label">
                  来源
                </label>
                <input
                  type="text"
                  id="source"
                  name="source"
                  value={filters.source}
                  onChange={handleFilterChange}
                  placeholder="按来源过滤"
                  className="filter-input"
                />
              </div>
              
              <div className="filter-group">
                <label htmlFor="dateFrom" className="filter-label">
                  开始日期
                </label>
                <input
                  type="date"
                  id="dateFrom"
                  name="dateFrom"
                  value={filters.dateFrom}
                  onChange={handleFilterChange}
                  className="filter-input"
                />
              </div>
              
              <div className="filter-group">
                <label htmlFor="dateTo" className="filter-label">
                  结束日期
                </label>
                <input
                  type="date"
                  id="dateTo"
                  name="dateTo"
                  value={filters.dateTo}
                  onChange={handleFilterChange}
                  className="filter-input"
                />
              </div>
              
              <button
                type="button"
                className="clear-filters"
                onClick={clearFilters}
              >
                清除过滤条件
              </button>
            </div>
          )}
        </div>
      </form>
    </div>
  );
};

export default SearchBar;
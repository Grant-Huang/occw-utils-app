// 共享的新增产品功能函数
// 用于手动生成报价单和报价单详情页面

let sharedProductCounter = 1;

function addNewProductShared(containerId, tableBodyId, counterId) {
    // 通用的新增产品行函数
    const tbody = document.getElementById(tableBodyId);
    const rowId = `add-row-${sharedProductCounter}`;
    
    const row = document.createElement('tr');
    row.id = rowId;
    row.innerHTML = `
        <td>
            <select class="form-select form-select-sm" onchange="onCategoryChangeShared(${sharedProductCounter})" id="category-${sharedProductCounter}">
                <option value="">选择类型</option>
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm" onchange="onProductChangeShared(${sharedProductCounter})" id="product-${sharedProductCounter}" disabled>
                <option value="">选择产品</option>
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm" onchange="onVariantChangeShared(${sharedProductCounter})" id="box-variant-${sharedProductCounter}" disabled>
                <option value="">选择柜身变体</option>
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm" onchange="onVariantChangeShared(${sharedProductCounter})" id="door-variant-${sharedProductCounter}" disabled>
                <option value="">选择门板变体</option>
            </select>
        </td>
        <td>
            <span id="sku-${sharedProductCounter}" class="badge bg-secondary">未选择</span>
        </td>
        <td>
            <span id="price-${sharedProductCounter}">$0.00</span>
        </td>
        <td>
            <input type="number" class="form-control form-control-sm" value="1" min="1" onchange="updateProductTotalShared(${sharedProductCounter})" id="qty-${sharedProductCounter}">
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-danger" onclick="removeProductShared(${sharedProductCounter})">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
    
    // 加载产品类别
    loadProductCategoriesShared(sharedProductCounter);
    
    sharedProductCounter++;
}

function loadProductCategoriesShared(rowNum) {
    // 加载产品类别
    $.ajax({
        url: '/get_product_categories',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const select = document.getElementById(`category-${rowNum}`);
                response.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    select.appendChild(option);
                });
            }
        },
        error: function() {
            showAlert('加载产品类别失败', 'warning');
        }
    });
}

function onCategoryChangeShared(rowNum) {
    // 处理类别选择变化
    const category = document.getElementById(`category-${rowNum}`).value;
    const productSelect = document.getElementById(`product-${rowNum}`);
    const boxVariantSelect = document.getElementById(`box-variant-${rowNum}`);
    const doorVariantSelect = document.getElementById(`door-variant-${rowNum}`);
    
    // 清空后续选择
    productSelect.innerHTML = '<option value="">选择产品</option>';
    boxVariantSelect.innerHTML = '<option value="">选择柜身变体</option>';
    doorVariantSelect.innerHTML = '<option value="">选择门板变体</option>';
    
    // 重置SKU和价格
    document.getElementById(`sku-${rowNum}`).textContent = '未选择';
    document.getElementById(`sku-${rowNum}`).className = 'badge bg-secondary';
    document.getElementById(`price-${rowNum}`).textContent = '$0.00';
    
    // 禁用后续选择
    productSelect.disabled = true;
    boxVariantSelect.disabled = true;
    doorVariantSelect.disabled = true;
    
    if (category) {
        // 加载产品
        loadProductsShared(rowNum, category);
    }
}

function loadProductsShared(rowNum, category) {
    // 根据类别加载产品列表
    $.ajax({
        url: '/get_products_by_category',
        type: 'GET',
        data: { category: category },
        success: function(response) {
            if (response.success) {
                const productSelect = document.getElementById(`product-${rowNum}`);
                const boxVariantSelect = document.getElementById(`box-variant-${rowNum}`);
                const doorVariantSelect = document.getElementById(`door-variant-${rowNum}`);
                
                // 填充产品选择
                productSelect.innerHTML = '<option value="">选择产品</option>';
                response.products.forEach(product => {
                    const option = document.createElement('option');
                    option.value = product;
                    option.textContent = product;
                    productSelect.appendChild(option);
                });
                productSelect.disabled = false;
                
                // 填充柜身变体选择，确保PLY在第一位
                boxVariantSelect.innerHTML = '<option value="">选择柜身变体</option>';
                
                // 先添加PLY选项（如果存在）
                if (response.box_variants.includes('PLY')) {
                    const plyOption = document.createElement('option');
                    plyOption.value = 'PLY';
                    plyOption.textContent = 'PLY';
                    boxVariantSelect.appendChild(plyOption);
                }
                
                // 添加其他变体选项
                response.box_variants.forEach(variant => {
                    if (variant !== 'PLY') {
                        const option = document.createElement('option');
                        option.value = variant;
                        option.textContent = variant;
                        boxVariantSelect.appendChild(option);
                    }
                });
                
                // 填充门板变体选择
                doorVariantSelect.innerHTML = '<option value="">选择门板变体</option>';
                response.door_variants.forEach(variant => {
                    const option = document.createElement('option');
                    option.value = variant;
                    option.textContent = variant;
                    doorVariantSelect.appendChild(option);
                });
                
                // 根据类别启用/禁用变体选择
                if (category === 'BOX') {
                    boxVariantSelect.disabled = false;
                    doorVariantSelect.disabled = false;
                } else if (category === 'Door' || category === 'ENDING PANEL' || category === 'MOLDING' || category === 'TOE KICK' || category === 'FILLER') {
                    boxVariantSelect.disabled = true;
                    doorVariantSelect.disabled = false;
                } else if (category === 'Assm.组合件') {
                    boxVariantSelect.disabled = false;
                    doorVariantSelect.disabled = false;
                } else if (category === 'HARDWARE') {
                    boxVariantSelect.disabled = true;
                    doorVariantSelect.disabled = true;
                }
            }
        },
        error: function() {
            showAlert('加载产品列表失败', 'warning');
        }
    });
}

function onProductChangeShared(rowNum) {
    // 处理产品选择变化
    searchSkuAndPriceShared(rowNum);
}

function onVariantChangeShared(rowNum) {
    // 变体选择改变时的处理
    searchSkuAndPriceShared(rowNum);
}

function searchSkuAndPriceShared(rowNum) {
    // 搜索SKU和价格
    const category = document.getElementById(`category-${rowNum}`).value;
    const product = document.getElementById(`product-${rowNum}`).value;
    const boxVariant = document.getElementById(`box-variant-${rowNum}`).value;
    const doorVariant = document.getElementById(`door-variant-${rowNum}`).value;
    
    if (!category || !product) {
        return;
    }
    
    $.ajax({
        url: '/search_sku_price',
        type: 'GET',
        data: {
            category: category,
            product: product,
            box_variant: boxVariant,
            door_variant: doorVariant
        },
        success: function(response) {
            if (response.success) {
                const skuElement = document.getElementById(`sku-${rowNum}`);
                const priceElement = document.getElementById(`price-${rowNum}`);
                
                if (response.found) {
                    skuElement.textContent = response.sku;
                    skuElement.className = 'badge bg-success';
                    priceElement.textContent = `$${response.price.toFixed(2)}`;
                } else {
                    skuElement.textContent = '未找到';
                    skuElement.className = 'badge bg-danger';
                    priceElement.textContent = '$0.00';
                }
                
                // 调用页面特定的更新函数
                if (typeof updateProductTotalShared === 'function') {
                    updateProductTotalShared(rowNum);
                }
            }
        },
        error: function() {
            showAlert('搜索SKU失败', 'warning');
        }
    });
}

function removeProductShared(rowNum) {
    // 删除产品行
    const row = document.getElementById(`add-row-${rowNum}`);
    if (row) {
        row.remove();
    }
}

function updateProductTotalShared(rowNum) {
    // 更新产品总价（需要页面特定实现）
    console.log('updateProductTotalShared called for row:', rowNum);
}

// 通用提示函数
function showAlert(message, type = 'info') {
    // 如果页面有showToast函数，使用它；否则使用alert
    if (typeof showToast === 'function') {
        showToast(message, type);
    } else if (typeof showAlert === 'function' && showAlert !== arguments.callee) {
        showAlert(message, type);
    } else {
        alert(message);
    }
}

// ===== 新增：通用产品加载函数 =====

/**
 * 重要通不要修改！通用产品加载函数，支持不同的元素ID前缀和功能模式
 * @param {string} category - 产品类别
 * @param {number} rowNum - 行号
 * @param {Object} options - 配置选项
 * @param {string} options.elementPrefix - 元素ID前缀，如 '' 或 'manual-'
 * @param {Object} options.savedValues - 已保存的值，用于设置选中状态
 * @param {Function} options.callback - 回调函数
 * @param {boolean} options.setValues - 是否设置已保存的值
 */
function loadProductsByCategoryUniversal(category, rowNum, options = {}) {
    const {
        elementPrefix = '',
        savedValues = null,
        callback = null,
        setValues = false
    } = options;
    
    const prefix = elementPrefix ? `${elementPrefix}-` : '';
    
    $.ajax({
        url: '/get_products_by_category',
        type: 'GET',
        data: { category: category },
        success: function(response) {
            if (response.success) {
                const productSelect = document.getElementById(`${prefix}product-${rowNum}`);
                const boxVariantSelect = document.getElementById(`${prefix}box-variant-${rowNum}`);
                const doorVariantSelect = document.getElementById(`${prefix}door-variant-${rowNum}`);
                
                if (!productSelect || !boxVariantSelect || !doorVariantSelect) {
                    console.error('Required elements not found for row:', rowNum);
                    return;
                }
                
                // 填充产品选择
                productSelect.innerHTML = '<option value="">选择产品</option>';
                response.products.forEach(product => {
                    const option = document.createElement('option');
                    option.value = product;
                    option.textContent = product;
                    
                    // 如果设置了保存值模式，设置选中状态
                    if (setValues && savedValues && savedValues.product === product) {
                        option.selected = true;
                    }
                    
                    productSelect.appendChild(option);
                });
                productSelect.disabled = false;
                
                // 填充柜身变体选择，确保PLY在第一位
                boxVariantSelect.innerHTML = '<option value="">选择柜身变体</option>';
                
                // 先添加PLY选项（如果存在）
                if (response.box_variants.includes('PLY')) {
                    const plyOption = document.createElement('option');
                    plyOption.value = 'PLY';
                    plyOption.textContent = 'PLY';
                    
                    if (setValues && savedValues && savedValues.box_variant === 'PLY') {
                        plyOption.selected = true;
                    }
                    
                    boxVariantSelect.appendChild(plyOption);
                }
                
                // 添加其他变体选项
                response.box_variants.forEach(variant => {
                    if (variant !== 'PLY') {
                        const option = document.createElement('option');
                        option.value = variant;
                        option.textContent = variant;
                        
                        if (setValues && savedValues && savedValues.box_variant === variant) {
                            option.selected = true;
                        }
                        
                        boxVariantSelect.appendChild(option);
                    }
                });
                
                // 填充门板变体选择
                doorVariantSelect.innerHTML = '<option value="">选择门板变体</option>';
                response.door_variants.forEach(variant => {
                    const option = document.createElement('option');
                    option.value = variant;
                    option.textContent = variant;
                    
                    if (setValues && savedValues && savedValues.door_variant === variant) {
                        option.selected = true;
                    }
                    
                    doorVariantSelect.appendChild(option);
                });
                
                // 根据类别启用/禁用变体选择
                if (category === 'BOX') {
                    boxVariantSelect.disabled = false;
                    doorVariantSelect.disabled = false;
                } else if (category === 'Door' || category === 'ENDING PANEL' || category === 'MOLDING' || category === 'TOE KICK' || category === 'FILLER') {
                    boxVariantSelect.disabled = true;
                    doorVariantSelect.disabled = false;
                } else if (category === 'Assm.组合件') {
                    boxVariantSelect.disabled = false;
                    doorVariantSelect.disabled = false;
                } else if (category === 'HARDWARE') {
                    boxVariantSelect.disabled = true;
                    doorVariantSelect.disabled = true;
                }
                
                // 如果有回调函数，调用它
                if (callback && typeof callback === 'function') {
                    callback(response);
                }
            }
        },
        error: function() {
            showAlert('加载产品列表失败', 'warning');
            if (callback && typeof callback === 'function') {
                callback(null);
            }
        }
    });
}

/**
 * 通用产品类别加载函数
 * @param {number} rowNum - 行号
 * @param {Object} options - 配置选项
 * @param {string} options.elementPrefix - 元素ID前缀
 * @param {Object} options.savedValues - 已保存的值
 * @param {Function} options.callback - 回调函数
 */
function loadProductCategoriesUniversal(rowNum, options = {}) {
    const {
        elementPrefix = '',
        savedValues = null,
        callback = null
    } = options;
    
    const prefix = elementPrefix ? `${elementPrefix}-` : '';
    
    $.ajax({
        url: '/get_product_categories',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const select = document.getElementById(`${prefix}category-${rowNum}`);
                if (!select) {
                    console.error('Category select element not found for row:', rowNum);
                    return;
                }
                
                response.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    
                    // 如果设置了保存值模式，设置选中状态
                    if (savedValues && savedValues.category === category) {
                        option.selected = true;
                    }
                    
                    select.appendChild(option);
                });
                
                // 如果有回调函数，调用它
                if (callback && typeof callback === 'function') {
                    callback(response);
                }
            }
        },
        error: function() {
            showAlert('加载产品类别失败', 'warning');
            if (callback && typeof callback === 'function') {
                callback(null);
            }
        }
    });
}
function searchSkuAndPriceUniversal(rowNum, elementPrefix = '') {
    const prefix = elementPrefix ? `${elementPrefix}-` : '';
    
    const category = document.getElementById(`${prefix}category-${rowNum}`).value;
    const product = document.getElementById(`${prefix}product-${rowNum}`).value;
    const boxVariant = document.getElementById(`${prefix}box-variant-${rowNum}`).value;
    const doorVariant = document.getElementById(`${prefix}door-variant-${rowNum}`).value;
    
    if (!category || !product) {
        return;
    }
    
    $.ajax({
        url: '/search_sku_price',
        type: 'GET',
        data: {
            category: category,
            product: product,
            box_variant: boxVariant,
            door_variant: doorVariant
        },
        success: function(response) {
            if (response.success) {
                const skuElement = document.getElementById(`${prefix}sku-${rowNum}`);
                const priceElement = document.getElementById(`${prefix}price-${rowNum}`);
                
                if (response.found) {
                    skuElement.textContent = response.sku;
                    skuElement.className = 'badge bg-success';
                    priceElement.textContent = `$${response.price.toFixed(2)}`;
                } else {
                    skuElement.textContent = '[[ t("not_found") ]]';
                    skuElement.className = 'badge bg-danger';
                    priceElement.textContent = '$0.00';
                }
                
                // 调用更新总计函数（如果存在）
                if (typeof updateManualTotal === 'function') {
                    updateManualTotal();
                } else if (typeof updateTotal === 'function') {
                    updateTotal();
                } else if (typeof updateProductTotalShared === 'function') {
                    updateProductTotalShared(rowNum);
                }
            }
        },
        error: function() {
            showAlert('[[ t("search_sku_failed") ]]', 'warning');
        }
    });
}

/**
 * 通用类别改变处理函数
 * @param {number} rowNum - 行号
 * @param {Object} options - 配置选项
 * @param {string} options.elementPrefix - 元素ID前缀，如 '' 或 'manual-'
 * @param {boolean} options.enableVariantLogic - 是否启用变体选择逻辑
 * @param {Function} options.customCallback - 自定义回调函数
 */
function onCategoryChangeUniversal(rowNum, options = {}) {
    const {
        elementPrefix = '',
        enableVariantLogic = true,
        customCallback = null
    } = options;
    
    const prefix = elementPrefix ? `${elementPrefix}-` : '';
    
    const category = document.getElementById(`${prefix}category-${rowNum}`).value;
    const productSelect = document.getElementById(`${prefix}product-${rowNum}`);
    const boxVariantSelect = document.getElementById(`${prefix}box-variant-${rowNum}`);
    const doorVariantSelect = document.getElementById(`${prefix}door-variant-${rowNum}`);
    
    // Clear subsequent selections
    productSelect.innerHTML = '<option value="">[[ t("select_product") ]]</option>';
    boxVariantSelect.innerHTML = '<option value="">[[ t("select_box_variant") ]]</option>';
    doorVariantSelect.innerHTML = '<option value="">[[ t("select_door_variant") ]]</option>';
    
    // Reset SKU and price
    document.getElementById(`${prefix}sku-${rowNum}`).textContent = '[[ t("not_selected") ]]';
    document.getElementById(`${prefix}sku-${rowNum}`).className = 'badge bg-secondary';
    document.getElementById(`${prefix}price-${rowNum}`).textContent = '$0.00';
    
    if (category) {
        productSelect.disabled = false;
        
        // 根据类型启用/禁用变体选择（如果启用）
        if (enableVariantLogic) {
            if (category === 'BOX') {
                boxVariantSelect.disabled = false;
                doorVariantSelect.disabled = false;
            } else if (category === 'Door' || category === 'ENDING PANEL' || category === 'MOLDING' || category === 'TOE KICK' || category === 'FILLER') {
                boxVariantSelect.disabled = true;
                doorVariantSelect.disabled = false;
            } else if (category === 'Assm.组合件') {
                boxVariantSelect.disabled = false;
                doorVariantSelect.disabled = false;
            } else if (category === 'HARDWARE') {
                boxVariantSelect.disabled = true;
                doorVariantSelect.disabled = true;
            }
        } else {
            // 如果禁用变体逻辑，则禁用所有变体选择
            boxVariantSelect.disabled = true;
            doorVariantSelect.disabled = true;
        }
        
        // Load products列表
        loadProductsByCategoryUniversal(category, rowNum, {
            elementPrefix: elementPrefix,
            setValues: false
        });
        
        // 如果有自定义回调函数，调用它
        if (customCallback && typeof customCallback === 'function') {
            customCallback(category, rowNum);
        }
    } else {
        productSelect.disabled = true;
        boxVariantSelect.disabled = true;
        doorVariantSelect.disabled = true;
    }
}

// 全局变量
let windows = new Map();
let projectCharts = new Map();
let crosshairSyncEnabled = true;
let oldLayout = '1x1';
let currentLayout = '1x1';
let windowCounter = 0;
let isDarkTheme = false;
let currentProject = '';
let currentStartDate = '';
let currentEndDate = '';
let tradeData = {};
let projectData = {};

// API基础URL
const API_BASE_URL = 'http://localhost:8800/api';

// 时间框架选项
const timeframes = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '1d', label: '日线' }
];

// 技术指标选项
const indicators = [
    { value: 'rsi', label: 'RSI(14)' },
    { value: 'macd', label: 'MACD' }
];

// 设置默认日期范围
function setDefaultDates() {
    const today = new Date();
    const oneYearAgo = new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000);
    
    document.getElementById('startDate').value = oneYearAgo.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
    
    currentStartDate = document.getElementById('startDate').value;
    currentEndDate = document.getElementById('endDate').value;
}

// 加载标的列表（支持 select 和 input+datalist 两种模式）
async function loadTargetList(window) {
    const typeSelector = window.element.querySelector('.type-selector');
    const type = typeSelector.value;
    const url = `${API_BASE_URL}/${type}`;

    const selector = window.element.querySelector('.symbol-selector');
    try {
        const response = await fetch(url);
        const data = await response.json();
        console.log('加载标的列表:', data);

        const symbols = Array.isArray(data.symbols) ? data.symbols : [];
        if (!selector) return;

        if (selector.tagName && selector.tagName.toLowerCase() === 'select') {
            selector.innerHTML = '<option value="">选择标的</option>';
            symbols.forEach(stock => {
                const option = document.createElement('option');
                option.value = stock;
                option.textContent = stock;
                selector.appendChild(option);
            });
        } else {
            // input + datalist 模式
            const windowId = window.windowId;
            const datalist = window.element.querySelector(`#symbolList_${windowId}`);
            if (datalist) {
                datalist.innerHTML = '';
                symbols.forEach(stock => {
                    const option = document.createElement('option');
                    option.value = stock;
                    datalist.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载标的列表失败:', error);
        showMessage('加载标的列表失败', 'error');
    }
}

function updateAllWindows() {
    windows.forEach((window, windowId) => {
        loadTargetData(window);
    });
}

// 加载标的数据
async function loadTargetData(window) {
    const windowId = window.windowId;
    const symbol = document.getElementById(`symbolSelector_${windowId}`).value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    currentProject = symbol;
    currentStartDate = startDate;
    currentEndDate = endDate;

    if (!window) {
        console.log(`窗口 ${windowId} 不存在`);
        return;
    }
    const type = window.type;
    const url = `${API_BASE_URL}/${type}/bars?symbol=${symbol}&start_date=${startDate}&end_date=${endDate}`;

    const indicator_url = `${API_BASE_URL}/${type}/indicators?symbol=${currentProject}&start_date=${currentStartDate}&end_date=${currentEndDate}&indicator=all_ma`;
    
    if (!symbol || !startDate || !endDate) {
        showMessage('请选择标的和日期范围', 'error');
        return;
    }
    
    try {
        // 加载candle数据
        const barsResponse = await fetch(url);
        const indicatorResponse = await fetch(indicator_url);
        const barsData = await barsResponse.json();
        const indicatorData = await indicatorResponse.json();
        
        if (!window) {
            console.log(`窗口 ${windowId} 不存在`);
            return;
        }
        if (barsData.bars) {
            updateBarsData(window, barsData.bars, indicatorData.indicator);
            updateVolumeData(window, barsData.bars);
        }
        requestAnimationFrame(() => {
            if (window.candleChart && window.candlestickSeries) {
                window.candleChart.timeScale().fitContent();
            }
            if (window.volumeChart && window.volumeSeries) {
                window.volumeChart.timeScale().fitContent();
            }
            if (window.indicatorChart && window.indicatorSeries) {
                window.indicatorChart.timeScale().fitContent();
            }

        });
        
    } catch (error) {
        console.error('加载标的数据失败:', error);
        showMessage('加载标的数据失败', 'error');
    }

    registerWindowsEvent(window);
}

// 更新窗口数据
function updateBarsData(window, barsData, maData) {
    
    if(!barsData) {
        console.log('candle数据为空');
        return;
    }
    
    // 转换数据格式
    const chartData = barsData.map(bar => ({
        time: bar.time,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close
    }));
    
    if (!window) {
        console.log(`窗口 ${window.windowId} 不存在`);
        return;
    }
    if (window.candleChart && window.candlestickSeries) {
        try {
            // 保存成交量数据到窗口对象

            window.candlestickSeries.setData(chartData);
            
            window.ma5_series.setData(maData.ma5);
            window.ma10_series.setData(maData.ma10);
            window.ma20_series.setData(maData.ma20);
            window.ma60_series.setData(maData.ma60);
            console.log(`窗口 ${window.windowId} candle数据已更新`);
        } catch (error) {
            console.error(`更新窗口 ${window.windowId} candle数据失败:`, error); 
        }
    }
    else {
        console.log('窗口或candlestickSeries不存在');
    }
}

// 更新成交量数据
function updateVolumeData(window, barsData) {
    if (!barsData) {
        console.log('成交量数据为空');
        return;
    }
    
    // 转换成交量数据格式
    const volumeData = barsData.map(bar => ({
        time: bar.time,
        value: bar.volume,
        color: bar.close >= bar.open ? '#ef5350' : '#26a69a' 
    }));
                
    // 更新所有窗口的成交量
    if (!window) {
        console.log(`窗口 ${window.windowId} 不存在`);
        return;
    }
    if (window.volumeChart && window.volumeSeries) {
        try {
            // 保存成交量数据到窗口对象
            window.volumeData = volumeData;
            window.volumeSeries.setData(volumeData);
            console.log(`窗口 ${window.windowId} 成交量已更新`);
        } catch (error) {
            console.error(`更新窗口 ${window.windowId} 成交量失败:`, error);
        }
    }
}

// 更新交易标记
function updateTradeMarkers(symbol) {
    const trades = tradeData[symbol] || [];
    
    windows.forEach((window, windowId) => {
        const chartContainer = window.element.querySelector('.chart-container');
        
        // 清除现有标记
        const existingMarkers = chartContainer.querySelectorAll('.trade-marker');
        existingMarkers.forEach(marker => marker.remove());
        
        // 添加新的交易标记
        trades.forEach(trade => {
            const marker = document.createElement('div');
            marker.className = `trade-marker ${trade.direction.toLowerCase()}`;
            marker.title = `${trade.direction} ${trade.volume} @ ${trade.price}`;
            
            // 这里需要根据时间计算位置
            // 简化处理，实际需要根据图表坐标计算
            marker.style.left = '50%';
            marker.style.top = '50%';
            
            chartContainer.appendChild(marker);
        });
    });
}


// 运行项目
function runProject() {
    toggleProjectPanel();
    loadProjects();
    createProjectCharts();
}

// 创建策略图表
let project_charts_created = false;
async function createProjectCharts() {
    if(project_charts_created) {
        return;
    }
    // 创建traded_symbol图表
    createTradedSymbolChart();

    // 创建Balance\drawdown\daily_pnl图表
    createPerformanceChart();

    const selector = document.getElementById('tradedSymbolSelector');
    selector.addEventListener('change', (e) => {
        const currentTradedSymbol = e.target.value;
        console.log('trade标的切换:', currentTradedSymbol);
        updateTradedSymbolChart(currentTradedSymbol);
    });

    project_charts_created = true;
}

async function createTradedSymbolChart() {
    const chartDiv = document.getElementById('tradedSymbolChart');
    const chart = LightweightCharts.createChart(chartDiv, {
        height: '80%',
        layout: {
            background: { color: '#1a202c' },
            textColor: '#ffffff',
        },
        grid: {
            vertLines: { color: '#2d3748' },
            horzLines: { color: '#2d3748' },
        },
    });
    chart.applyOptions({
        rightPriceScale: {
            visible: true,
        },
    });
    
    const trade_candlestickSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
        title: 'candlestick',
        upColor: '#ef5350',
        downColor: '#26a69a',
        borderVisible: false,
        wickUpColor: '#ef5350',
        wickDownColor: '#26a69a',
    });
    trade_candlestickSeries.priceScale().applyOptions({
            scaleMargins: {
                top: 0.1,
                bottom: 0.2,
            },
        });

    const trade_volumeSeries = chart.addSeries(LightweightCharts.HistogramSeries, {
        title: 'volume',
        priceFormat: {
            type: 'volume',
        },
        priceScaleId: ''
    });
    trade_volumeSeries.priceScale().applyOptions({
        scaleMargins: {
            top: 0.7,
            bottom: 0.0,
        },
    });
        
    projectCharts.set('tradedSymbolChart', chart);
    projectCharts.set('trade_candlestickSeries', trade_candlestickSeries);
    projectCharts.set('trade_volumeSeries', trade_volumeSeries);
}

let isProjectResizing = false;
let tradeDataLoaded = false;
function sync_project_charts() {
    const tradechart = projectCharts.get('tradedSymbolChart');
    const balanceChart = projectCharts.get('balanceChart');
    const drawdownChart = projectCharts.get('drawdownChart');
    const daily_pnlChart = projectCharts.get('dailyPnlChart');
    const trade_candlestickSeries = projectCharts.get('trade_candlestickSeries');
    const balanceSeries = projectCharts.get('balanceSeries');
    const drawdownSeries = projectCharts.get('drawdownSeries');
    const daily_pnlSeries = projectCharts.get('daily_pnlSeries');

    

    tradechart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if(!isProjectResizing && timeRange) {
            isProjectResizing = true;
            balanceChart.timeScale().setVisibleRange(timeRange);
            drawdownChart.timeScale().setVisibleRange(timeRange);
            daily_pnlChart.timeScale().setVisibleRange(timeRange);
        }
        requestAnimationFrame(() => {
            isProjectResizing = false;
        });
    });

    balanceChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if(!isProjectResizing && timeRange) {
            isProjectResizing = true;
            if(tradechart && trade_candlestickSeries && tradeDataLoaded) tradechart.timeScale().setVisibleRange(timeRange);
            if(daily_pnlChart && daily_pnlSeries) daily_pnlChart.timeScale().setVisibleRange(timeRange);
            if(drawdownChart && drawdownSeries) drawdownChart.timeScale().setVisibleRange(timeRange);
        }
        requestAnimationFrame(() => {
            isProjectResizing = false;
        });
        
    });
    daily_pnlChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if(!isProjectResizing && timeRange) {
            isProjectResizing = true;
            if(tradechart && trade_candlestickSeries && tradeDataLoaded) tradechart.timeScale().setVisibleRange(timeRange);
            if(balanceChart && balanceSeries) balanceChart.timeScale().setVisibleRange(timeRange);
            if(drawdownChart && drawdownSeries) drawdownChart.timeScale().setVisibleRange(timeRange);
        }
        requestAnimationFrame(() => {
            isProjectResizing = false;
        });
    });
    drawdownChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if(!isProjectResizing && timeRange) {
            isProjectResizing = true;
            if(tradechart && trade_candlestickSeries && tradeDataLoaded) tradechart.timeScale().setVisibleRange(timeRange);
            if(balanceChart && balanceSeries) balanceChart.timeScale().setVisibleRange(timeRange);
            if(daily_pnlChart && daily_pnlSeries) daily_pnlChart.timeScale().setVisibleRange(timeRange);
        }
        requestAnimationFrame(() => {
            isProjectResizing = false;
        });
    });


    tradechart.subscribeCrosshairMove((param) => {
        if(param.time) {
            if(balanceChart && balanceSeries) balanceChart.setCrosshairPosition(0, param.time, balanceSeries);
            if(drawdownChart && drawdownSeries) drawdownChart.setCrosshairPosition(0, param.time, drawdownSeries);
            if(daily_pnlChart && daily_pnlSeries) daily_pnlChart.setCrosshairPosition(0, param.time, daily_pnlSeries);
            return;
        }
    });
    balanceChart.subscribeCrosshairMove((param) => {
        if(param.time) {
            if(tradechart && trade_candlestickSeries && tradeDataLoaded) tradechart.setCrosshairPosition(0, param.time, trade_candlestickSeries);
            if(drawdownChart && drawdownSeries) drawdownChart.setCrosshairPosition(0, param.time, drawdownSeries);
            if(daily_pnlChart && daily_pnlSeries) daily_pnlChart.setCrosshairPosition(0, param.time, daily_pnlSeries);
            return;
        }
    });
    drawdownChart.subscribeCrosshairMove((param) => {
        if(param.time) {
            if(balanceChart && balanceSeries) balanceChart.setCrosshairPosition(0, param.time, balanceSeries);
            if(tradechart && trade_candlestickSeries && tradeDataLoaded) tradechart.setCrosshairPosition(0, param.time, trade_candlestickSeries);
            if(daily_pnlChart && daily_pnlSeries) daily_pnlChart.setCrosshairPosition(0, param.time, daily_pnlSeries);
            return;
        }
    });
    daily_pnlChart.subscribeCrosshairMove((param) => {
        if(param.time) {
            if(balanceChart && balanceSeries) balanceChart.setCrosshairPosition(0, param.time, balanceSeries);
            if(drawdownChart && drawdownSeries) drawdownChart.setCrosshairPosition(0, param.time, drawdownSeries);
            if(tradechart && trade_candlestickSeries && tradeDataLoaded) tradechart.setCrosshairPosition(0, param.time, trade_candlestickSeries);
            return;
        }
    });
}

async function updateProjectTradedSymbolList() {
    const response = await fetch(`${API_BASE_URL}/trades/${currentProject}/symbol_list`);
    const symbol_list = await response.json();
    if (symbol_list.trades_symbol_list && symbol_list.trades_symbol_list.length > 0) {
        const selector = document.getElementById('tradedSymbolSelector');
        symbol_list.trades_symbol_list.forEach(async (symbol) => {
            const option = document.createElement('option');
            option.value = symbol;
            option.textContent = symbol;
            selector.appendChild(option);
        });
    }
}

async function updateProjectCharts(strategyData) {
    // 更新traded_symbol图表
    updateProjectTradedSymbolList();

    // 更新Balance\drawdown\daily_pnl图表
    if(strategyData.balance && strategyData.balance.length > 0) {
        updateBalanceChart(strategyData.time, strategyData.balance);
    }
    if(strategyData.drawdown && strategyData.drawdown.length > 0) {
        updateDrawdownChart(strategyData.time, strategyData.drawdown);
    }
    if(strategyData.daily_pnl && strategyData.daily_pnl.length > 0) {
        updateDailyPnlChart(strategyData.time, strategyData.daily_pnl);
    }

    requestAnimationFrame(() => {
        sync_project_charts();
    });
}

function oneMonthBefore(iso) {
    const base = iso ? new Date(iso) : new Date();
    const y = base.getFullYear(), m = base.getMonth(), d = base.getDate();
    const daysInPrev = new Date(y, m, 0).getDate();
    const prev = new Date(y, m - 1, Math.min(d, daysInPrev));
    const mm = String(prev.getMonth() + 1).padStart(2, '0');
    const dd = String(prev.getDate()).padStart(2, '0');
    return `${prev.getFullYear()}-${mm}-${dd}`;
}

function oneMonthAfter(iso) {
    const base = iso ? new Date(iso) : new Date();
    const y = base.getFullYear(), m = base.getMonth(), d = base.getDate();
    const daysInNext = new Date(y, m + 1, 0).getDate();
    const next = new Date(y, m + 1, Math.min(d, daysInNext));
    const mm = String(next.getMonth() + 1).padStart(2, '0');
    const dd = String(next.getDate()).padStart(2, '0');
    return `${next.getFullYear()}-${mm}-${dd}`;
}
let last_marker;
async function updateTradedSymbolChart(symbol) {
    const response = await fetch(`${API_BASE_URL}/trades/${currentProject}/data?symbol=${symbol}`);
    const trades_data = await response.json();
    const volume_data = [];
    const candlestick_data = [];
    console.log('trades_data', trades_data);
    if (trades_data.trades && trades_data.trades.length > 0) {

        const project_summary_response = await fetch(`${API_BASE_URL}/project/${currentProject}`);
        const project_summary = await project_summary_response.json();
        const left_date = oneMonthBefore(project_summary.project.start_time);
        const right_date = oneMonthAfter(project_summary.project.end_time);
        
        const bar_data_response = await fetch(`${API_BASE_URL}/zh_stocks/bars?symbol=${symbol}&start_date=${left_date}&end_date=${right_date}`);
        const bar_data = await bar_data_response.json();
        if (bar_data.bars && bar_data.bars.length > 0) {
            for(let i = 0; i < bar_data.bars.length; i++) {
                volume_data.push({
                    time: bar_data.bars[i].time,
                    value: bar_data.bars[i].volume
                });
                candlestick_data.push({
                    time: bar_data.bars[i].time,
                    open: bar_data.bars[i].open,
                    high: bar_data.bars[i].high,
                    low: bar_data.bars[i].low,
                    close: bar_data.bars[i].close
                });
            }
        }

        const chart = projectCharts.get('tradedSymbolChart');
        const trade_candlestickSeries = projectCharts.get('trade_candlestickSeries');
        const trade_volumeSeries = projectCharts.get('trade_volumeSeries');
        const marker = trades_data.trades.map(trade => ({
            time: trade.time,
            position: trade.direction === 'LONG' ? 'belowBar' : 'aboveBar',
            shape: trade.direction === 'LONG' ? 'arrowUp' : 'arrowDown',
            color: trade.direction === 'LONG' ? '#ef5350' : '#26a69a',
            text: trade.direction === 'LONG' ? 'Buy @ ' + trade.price : 'Sell @ ' + trade.price,
        }));
        if(last_marker) {
            last_marker.setMarkers([]);
        }
        const seriesMarker = LightweightCharts.createSeriesMarkers(trade_candlestickSeries);                
        seriesMarker.setMarkers(marker);
        trade_candlestickSeries.setData(candlestick_data);
        trade_volumeSeries.setData(volume_data);
        if(candlestick_data.length > 0 && volume_data.length > 0) tradeDataLoaded = true;
        else tradeDataLoaded = false;
        last_marker = seriesMarker;
        chart.timeScale().fitContent();
    }
    
    console.log('更新交易标的图表:', symbol);
}

function createPerformanceChart() {
    const balance_container = document.getElementById('balanceChartContainer');
    const drawdown_container = document.getElementById('drawdownChartContainer');
    const daily_pnl_container = document.getElementById('dailyPnlChartContainer');

    const balance_chartDiv = document.getElementById('balanceChart');
    const drawdown_chartDiv = document.getElementById('drawdownChart');
    const daily_pnl_chartDiv = document.getElementById('dailyPnlChart');

    if (!balance_container || !balance_chartDiv || !drawdown_container || !drawdown_chartDiv || !daily_pnl_container || !daily_pnl_chartDiv) {
        console.error('Balance/drawdown/daily_pnl图表容器元素不存在');
        return;
    }
    // 显示容器
    balance_container.style.display = 'block';
    drawdown_container.style.display = 'block';
    daily_pnl_container.style.display = 'block';
    
    try {
        // 创建新图表
        balanceChart = LightweightCharts.createChart(balance_chartDiv, {
            layout: {
                background: { color: '#1a202c' },
                textColor: '#ffffff',
            },
            grid: {
                vertLines: { color: '#2d3748' },
                horzLines: { color: '#2d3748' },
            },
            rightPriceScale: {
                borderColor: '#4a5568',
            },
            timeScale: {
                borderColor: '#4a5568',
                timeVisible: true,
                secondsVisible: false,
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Magnet,
            },
        });
        
        drawdownChart = LightweightCharts.createChart(drawdown_chartDiv, {
            layout: {
                background: { color: '#1a202c' },
                textColor: '#ffffff',
            },
            grid: {
                vertLines: { color: '#2d3748' },
                horzLines: { color: '#2d3748' },
            },
            rightPriceScale: {
                borderColor: '#4a5568',
            },
            timeScale: {
                borderColor: '#4a5568',
                timeVisible: true,
                secondsVisible: false,
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Magnet,
            },
        });

        daily_pnlChart = LightweightCharts.createChart(daily_pnl_chartDiv, {
            layout: {
                background: { color: '#1a202c' },
                textColor: '#ffffff',
            },
            grid: {
                vertLines: { color: '#2d3748' },
                horzLines: { color: '#2d3748' },
            },
            rightPriceScale: {
                borderColor: '#4a5568',
            },
            timeScale: {
                borderColor: '#4a5568',
                timeVisible: true,
                secondsVisible: false,
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Magnet,
            },
        });
        
        // 添加线条系列
        const balanceSeries = balanceChart.addSeries(LightweightCharts.LineSeries, {
            color: '#26a69a',
            lineWidth: 2,
            title: '账户余额'
        });

        const drawdownSeries = drawdownChart.addSeries(LightweightCharts.LineSeries, {
            color: '#ef5350',
            lineWidth: 2,
            title: '回撤率'
        });

        const daily_pnlSeries = daily_pnlChart.addSeries(LightweightCharts.HistogramSeries, {
            color: '#26a69a',
            lineWidth: 2,
            title: '每日盈亏'
        });

        projectCharts.set('balanceChart', balanceChart);
        projectCharts.set('drawdownChart', drawdownChart);
        projectCharts.set('dailyPnlChart', daily_pnlChart);
        projectCharts.set('balanceSeries', balanceSeries);
        projectCharts.set('drawdownSeries', drawdownSeries);
        projectCharts.set('daily_pnlSeries', daily_pnlSeries);
    } catch (error) {
        console.error('创建Balance/drawdown/daily_pnl图表失败:', error);
    }
}

// 创建Balance曲线图表
function updateBalanceChart(timeData, balanceData) {
    if(timeData.length !== balanceData.length) {
        console.error('时间数据和余额数据长度不一致');
        return;
    }

    // 设置数据
    const chartData = [];
    for(let i = 0; i < balanceData.length; i++) {
        chartData.push({
            time: timeData[i],
            value: balanceData[i]
        });
    }

    const balanceSeries = projectCharts.get('balanceSeries');
    const balanceChart = projectCharts.get('balanceChart');
    balanceSeries.setData(chartData);
    balanceChart.timeScale().fitContent();
    
    console.log('Balance图表更新成功，数据点数:', chartData.length);    
}

// 创建Drawdown曲线图表
function updateDrawdownChart(timeData, drawdownData) {
    if(timeData.length !== drawdownData.length) {
        console.error('时间数据和回撤数据长度不一致');
        return;
    }

    // 设置数据
    const chartData = [];
    for(let i = 0; i < drawdownData.length; i++) {
        chartData.push({
            time: timeData[i],
            value: drawdownData[i]
        });
    }
    
    const drawdownSeries = projectCharts.get('drawdownSeries');
    const drawdownChart = projectCharts.get('drawdownChart');
    drawdownSeries.setData(chartData);
    drawdownChart.timeScale().fitContent();
    console.log('Drawdown图表更新成功，数据点数:', chartData.length);
}

// 创建Daily_pnl图表
function updateDailyPnlChart(timeData, dailyPnlData) {
    if(timeData.length !== dailyPnlData.length) {
        console.error('时间数据和daily_pnl数据长度不一致');
        return;
    }
        
    // 设置数据
    const chartData = [];
    for(let i = 0; i < dailyPnlData.length; i++) {
        chartData.push({
            time: timeData[i],
            value: dailyPnlData[i]
        });
    }
    
    const daily_pnlSeries = projectCharts.get('daily_pnlSeries');
    const daily_pnlChart = projectCharts.get('dailyPnlChart');
    daily_pnlSeries.setData(chartData);
    daily_pnlChart.timeScale().fitContent();
    console.log('Daily_pnl图表更新成功，数据点数:', chartData.length);  
}

// 打开项目图表面板
function toggleProjectChartPanel() {
    const panel = document.getElementById('projectChartPanel');
    const toVisible = panel.style.display == 'none';
    panel.style.display = toVisible ? 'block' : 'none';

    const chartDiv = document.getElementById('tradedSymbolChart');
    const balance_chartDiv = document.getElementById('balanceChart');
    const drawdown_chartDiv = document.getElementById('drawdownChart');
    const daily_pnl_chartDiv = document.getElementById('dailyPnlChart');

    projectCharts.get('tradedSymbolChart').applyOptions({
        height: toVisible ? chartDiv.clientHeight : '0',
        width: toVisible ? chartDiv.clientWidth : '0',
    });
    projectCharts.get('tradedSymbolChart').timeScale().fitContent();
    projectCharts.get('balanceChart').applyOptions({
        height: toVisible ? balance_chartDiv.clientHeight : '0',
        width: toVisible ? balance_chartDiv.clientWidth : '0',
    });
    projectCharts.get('balanceChart').timeScale().fitContent();
    projectCharts.get('drawdownChart').applyOptions({
        height: toVisible ? drawdown_chartDiv.clientHeight : '0',
        width: toVisible ? drawdown_chartDiv.clientWidth : '0',
    });
    projectCharts.get('drawdownChart').timeScale().fitContent();
    projectCharts.get('dailyPnlChart').applyOptions({
        height: toVisible ? daily_pnl_chartDiv.clientHeight : '0',
        width: toVisible ? daily_pnl_chartDiv.clientWidth : '0',
    });
    projectCharts.get('dailyPnlChart').timeScale().fitContent();
}

// 打开项目面板
function toggleProjectPanel() {
    const panel = document.getElementById('projectPanel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

// 加载项目列表
async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE_URL}/projects`);
        const data = await response.json();
        
        if (data.projects) {
            projectData = {};
            const projectSelector = document.getElementById('projectSelector');
            
            // 清空现有内容
            projectSelector.innerHTML = '<option value="">选择项目...</option>';
            
            if (data.projects.length === 0) {
                projectSelector.innerHTML = '<option value="">暂无注册的项目</option>';
                return;
            }
            
            // 添加到选择器
            data.projects.forEach(projectName => {
                const option = document.createElement('option');
                option.value = projectName;
                option.textContent = projectName;
                projectSelector.appendChild(option);
            });
            
            showMessage(`成功加载 ${data.projects.length} 个项目`, 'success');
        }
    } catch (error) {
        console.error('加载项目列表失败:', error);
        showMessage('加载项目列表失败', 'error');
    }
}

// 选择项目
async function selectProject(projectName) {
    try {
        currentProject = projectName;
        
        // 加载项目详情
        const response = await fetch(`${API_BASE_URL}/project/${projectName}`);
        const data = await response.json();
        
        if (data.project) {
            projectData[projectName] = data.project;
            updateProjectSummary(projectName);
        }
        
        // 加载项目策略数据
        const strategyResponse = await fetch(`${API_BASE_URL}/project/${projectName}/data`);
        const strategyData = await strategyResponse.json();
        
        if (strategyData.strategy_data) {
            projectData[projectName].strategy_data = strategyData.strategy_data;
            updateProjectPerformance(projectName);
        }
        
    } catch (error) {
        console.error('加载项目详情失败:', error);
        showMessage('加载项目详情失败', 'error');
    }
}

// 更新项目详情
function updateProjectSummary(projectName) {
    const detailsDiv = document.getElementById('projectDetails');
    const project_data = projectData[projectName];
    
    if (!project_data) {
        detailsDiv.innerHTML = '<p>项目数据加载失败</p>';
        return;
    }
    
    let html = `<h4>${projectName}</h4>`;
    html += `<div class="project-stats">`;
    
    if (project_data.status) {
        html += `<div class="stat-item">
            <div class="stat-value">${project_data.status}</div>
            <div class="stat-label">状态</div>
        </div>`;
    }
    
    if (project_data.trades_count !== undefined) {
        html += `<div class="stat-item">
            <div class="stat-value">${project_data.trades_count}</div>
            <div class="stat-label">交易次数</div>
        </div>`;
    }

    if (project_data.sharpe_ratio !== undefined) {
        html += `<div class="stat-item">
            <div class="stat-value">${project_data.sharpe_ratio.toFixed(2)}</div>
            <div class="stat-label">夏普比率</div>
        </div>`;
    }

    if (project_data.win_rate !== undefined) {
        html += `<div class="stat-item">
            <div class="stat-value">${project_data.win_rate.toFixed(2)}</div>
            <div class="stat-label">胜率</div>
        </div>`;
    }

    if (project_data.initial_capital !== undefined) {
        html += `<div class="stat-item">
            <div class="stat-value">${project_data.initial_capital.toFixed(2)}</div>
            <div class="stat-label">初始金额</div>
        </div>`;
    }
    
    if (project_data.total_pnl !== undefined) {
        const pnlColor = project_data.total_pnl >= 0 ? '#26a69a' : '#ef5350';
        html += `<div class="stat-item">
            <div class="stat-value" style="color: ${pnlColor}">${project_data.total_pnl.toFixed(2)}</div>
            <div class="stat-label">总收益</div>
        </div>`;
    }

    if (project_data.final_balance !== undefined) {
        html += `<div class="stat-item">
            <div class="stat-value">${project_data.final_balance.toFixed(2)}</div>
            <div class="stat-label">最终余额</div>
        </div>`;
    }

    if (project_data.max_drawdown !== undefined) {
        html += `<div class="stat-item">
            <div class="stat-value" style="color: #ef5350">${project_data.max_drawdown.toFixed(2)}%</div>
            <div class="stat-label">最大回撤</div>
        </div>`;
    }
    
    if (project_data.max_drawdown_duration !== undefined) {
        html += `<div class="stat-item">
            <div class="stat-value" style="color: #ef5350">${project_data.max_drawdown_duration.toFixed(2)}</div>
            <div class="stat-label">最大回撤持续时间</div>
        </div>`;
    }
    
    html += `</div>`;
    
    if (project_data.start_time && project_data.end_time) {
        html += `<p><small>运行时间: ${project_data.start_time} 至 ${project_data.end_time}</small></p>`;
    }
    
    detailsDiv.innerHTML = html;
}

// 更新项目性能图表
function updateProjectPerformance(projectName) {
    const project_data = projectData[projectName];
    if (!project_data || !project_data.strategy_data) return;
    
    const strategyData = project_data.strategy_data;
    
    // 添加交易记录显示
    if (strategyData.trades && strategyData.trades.length > 0) {
        addTradeRecordsToDetails(projectName, strategyData.trades);
    }

    updateProjectCharts(strategyData);
}

// 添加交易记录到详情
function addTradeRecordsToDetails(projectName, trades) {
    const detailsDiv = document.getElementById('projectDetails');
    const existingContent = detailsDiv.innerHTML;
    
    let html = existingContent;
    html += `<div class="project-item" style="margin-top: 15px;">
        <h4>📋 最近交易记录</h4>
        <div style="max-height: 150px; overflow-y: auto;">`;
    
    // 显示最近10笔交易
    // const recentTrades = trades.slice(-10).reverse();
    const recentTrades = trades;
    recentTrades.forEach(trade => {
        const tradeTime = new Date(trade.time * 1000).toLocaleString();
        const directionColor = trade.direction === 'LONG' ? '#26a69a' : '#ef5350';
        const directionText = trade.direction === 'LONG' ? '买入' : '卖出';
        
        html += `<div style="padding: 5px; margin: 2px 0; background: #2d3748; border-radius: 3px; font-size: 11px;">
            <span style="color: ${directionColor};">${directionText}</span> 
            ${trade.symbol} ${trade.volume}股 @ ${trade.price}
            <br><small style="color: #a0aec0;">${tradeTime}</small>
        </div>`;
    });
    
    html += `</div>
        <p><small>共${trades.length}笔</small></p>
    </div>`;
    
    detailsDiv.innerHTML = html;
}

// 项目选择事件处理
function onProjectSelect() {
    const projectName = document.getElementById('projectSelector').value;
    if (projectName) {
        selectProject(projectName);
    }
}

// 执行项目运行
async function executeRunProject() {
    const projectName = document.getElementById('projectSelector').value;
    const startDate = document.getElementById('projectStartDate').value;
    const endDate = document.getElementById('projectEndDate').value;
    
    if (!projectName || !startDate || !endDate) {
        showMessage('请选择项目和日期范围', 'error');
        return;
    }
    
    try {
        showMessage('正在运行项目，请稍候...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/run_project`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_name: projectName,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`项目 ${projectName} 运行成功`, 'success');
            if (currentProject === projectName) {
                selectProject(projectName);
            }
        } else {
            showMessage(`项目运行失败: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('运行项目失败:', error);
        showMessage('运行项目失败', 'error');
    }
}

// 重新加载项目
async function reloadProjects() {
    try {
        showMessage('正在重新加载项目...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/reload_projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('项目重新加载成功', 'success');
            // 重新加载项目列表
            loadProjects();
        } else {
            showMessage(`重新加载失败: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('重新加载项目失败:', error);
        showMessage('重新加载项目失败', 'error');
    }
}

// 显示消息
function showMessage(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'error' ? 'error-message' : 
                          type === 'info' ? 'info-message' : 'success-message';
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

// 初始化布局
function initLayout() {
    const layoutSelector = document.getElementById('layoutSelector');
    layoutSelector.addEventListener('change', (e) => {
        oldLayout = currentLayout;
        currentLayout = e.target.value;
        console.log('布局切换:', currentLayout);
        updateLayout();
    });
    
    // 添加日期选择器事件监听
    document.getElementById('startDate').addEventListener('change', (e) => {
        currentStartDate = e.target.value;
    });
    
    document.getElementById('endDate').addEventListener('change', (e) => {
        currentEndDate = e.target.value;
    });
    
}

// 更新布局
function updateLayout() {
    const grid = document.getElementById('windowGrid');
    if (!grid) {
        console.error('找不到windowGrid元素');
        return;
    }
    
    grid.className = `window-grid layout-${currentLayout}`;
    
    const maxWindows = getMaxWindowsForLayout(currentLayout);
    const currentWindows = windows.size;
    
    console.log('更新布局:', {
        layout: currentLayout,
        maxWindows: maxWindows,
        currentWindows: currentWindows
    });
    
    if (currentWindows < maxWindows) {
        console.log('创建新窗口:', maxWindows - currentWindows);
        for (let i = currentWindows; i < maxWindows; i++) {
            createWindow();
        }
    } else if (currentWindows > maxWindows) {
        console.log('销毁多余窗口:', currentWindows - maxWindows);
        const windowIds = Array.from(windows.keys());
        // 从最后一个窗口开始销毁
        for (let i = windowIds.length - 1; i >= maxWindows; i--) {
            destroyWindow(windowIds[i]);
        }
    }
    
    // 强制重新布局
    setTimeout(() => {
        forceRelayout();
    }, 200);
}

// 强制重新布局 - 适配三子图布局
let isResizing = false;
function forceRelayout() {
    const grid = document.getElementById('windowGrid');
    if (grid) {
        // 触发重新计算布局
        grid.style.display = 'none';
        grid.style.display = 'grid';
        grid.classList.remove(`layout-${oldLayout}`);
        grid.classList.add(`layout-${currentLayout}`);
        grid.offsetHeight; // 强制重排

        
        // 确保所有窗口都有正确的尺寸
        windows.forEach((window, windowId) => {
            try {
                chart_window = document.getElementById(`${windowId}`);
                chart_container = document.getElementById(`chart-container_${windowId}`);
                const header = document.querySelector('.window-header');
                const status_bar = document.querySelector('.status-bar');

                chart_container.style.width = chart_window.clientWidth - header.clientHeight - status_bar.clientHeight + 'px';
                chart_container.style.height = chart_window.clientHeight - header.clientHeight - status_bar.clientHeight + 'px';

                // 获取子图容器
                const candleContainer = document.getElementById(`candle_${windowId}`);
                const volumeContainer = document.getElementById(`volume_${windowId}`);
                const indicatorContainer = document.getElementById(`indicator_${windowId}`);
                
                // 调整三个子图的尺寸
                const newCandleWidth = candleContainer.clientWidth;
                const newCandleHeight = candleContainer.clientHeight;
                const newVolumeWidth = volumeContainer.clientWidth;
                const newVolumeHeight = volumeContainer.clientHeight;
                const newIndicatorWidth = indicatorContainer.clientWidth;
                const newIndicatorHeight = indicatorContainer.clientHeight;
                console.log(`🔄 重排后窗口 ${windowId} 尺寸: ${newCandleWidth} x ${newCandleHeight}`);
                isResizing = true;
                if (window.candleChart && candleContainer) {
                    window.candleChart.applyOptions({
                        width: newCandleWidth,
                        height: newCandleHeight,
                    });
                }
                

                if (window.volumeChart && volumeContainer) {
                    window.volumeChart.applyOptions({
                        width: newVolumeWidth,
                        height: newVolumeHeight,
                    });
                }
                
                if (window.indicatorChart && indicatorContainer) {
                    window.indicatorChart.applyOptions({
                        width: newIndicatorWidth,
                        height: newIndicatorHeight,
                    });
                }
                
                console.log(`窗口 ${windowId} 重新布局完成`);
            } catch (error) {
                console.error(`窗口 ${windowId} 重新布局失败:`, error);
            }
        });

        windows.forEach((window, windowId) => {
            if (window.candleChart && window.candlestickSeries) {
                window.candleChart.timeScale().fitContent();
            }
            if (window.volumeChart && window.volumeSeries) {
                window.volumeChart.timeScale().fitContent();
            }
            if (window.indicatorChart && window.indicatorSeries) {
                window.indicatorChart.timeScale().fitContent();
            }
        });
        
        // console.log('强制重新布局完成，窗口数:', windows.size);
    }
}

// 获取布局的最大窗口数
function getMaxWindowsForLayout(layout) {
    switch(layout) {
        case '1x1': return 1;
        case '1x2': return 2;
        case '2x2': return 4;
        case '2x3': return 6;
        default: return 1;
    }
}

// 创建初始窗口
function createInitialWindows() {
    const maxWindows = getMaxWindowsForLayout(currentLayout);
    for (let i = 0; i < maxWindows; i++) {
        createWindow();
    }
}

// 创建新窗口
function createWindow() {
    const windowId = `window_${++windowCounter}`;
    // 默认使用日线
    const timeframe = timeframes.find(tf => tf.value === '1d') || timeframes[0];
    
    console.log('创建窗口:', { windowId, timeframe: timeframe.value });
    
    const windowElement = createWindowElement(windowId, timeframe);
    
    const grid = document.getElementById('windowGrid');
    if (grid) {
        grid.appendChild(windowElement);
        console.log('窗口元素已添加到DOM:', windowId);
    } else {
        console.error('找不到windowGrid元素');
        return null;
    }
    
    // 延迟创建图表，确保DOM元素已渲染
    setTimeout(() => {
        createChart(windowId, windowElement, timeframe.value);
    }, 100);
    
    console.log('窗口创建完成:', windowId, '当前窗口数:', windows.size);
    
    return windowId;
}

// 创建窗口HTML元素
function createWindowElement(windowId, timeframe) {
    const windowDiv = document.createElement('div');
    windowDiv.className = 'chart-window';
    windowDiv.id = windowId;
    
    windowDiv.innerHTML = `
        <div class="window-header">
            <div class="window-title"> 标的 </div>
            <div class="window-controls">
                <select class="type-selector" id="typeSelector_${windowId}" onchange="changeType('${windowId}', this.value)">
                    <option value="zh_stocks" selected>zh_stocks</option>
                    <option value="zh_indexs">zh_indexs</option>
                </select>
                <input list="symbolList_${windowId}" class="symbol-selector" id="symbolSelector_${windowId}" placeholder="输入或选择标的" />
                <datalist id="symbolList_${windowId}"></datalist>
                <select class="timeframe-selector" onchange="changeTimeframe('${windowId}', this.value)">
                    ${timeframes.map(tf => 
                        `<option value="${tf.value}" ${tf.value === timeframe.value ? 'selected' : ''}>${tf.label}</option>`
                    ).join('')}
                </select>
                <select class="indicator-selector" onchange="updateIndicator('${windowId}', this.value)">
                    <option value="选择指标">选择指标</option>
                    ${indicators.map(ind => 
                        `<option value="${ind.value}">${ind.label}</option>`
                    ).join('')}
                </select>
                <button class="close-btn" onclick="destroyWindow('${windowId}')">×</button>
            </div>
        </div>
        <div class="chart-container" id="chart-container_${windowId}">
            <div class="subchart-container">
                <div class="subchart candle" id="candle_${windowId}"></div>
                <div class="subchart volume" id="volume_${windowId}"></div>
                <div class="subchart indicator" id="indicator_${windowId}"></div>
            </div>
        </div>
        <div class="status-bar">
            <span>就绪</span>
            <span class="sync-indicator ${crosshairSyncEnabled ? '' : 'inactive'}">
                ${crosshairSyncEnabled ? '同步开启' : '同步关闭'}
            </span>
        </div>
    `;
    
    return windowDiv;
}

// 创建图表
function createChart(windowId, windowElement, timeframe) {
    const candleContainer = document.getElementById(`candle_${windowId}`);
    const volumeContainer = document.getElementById(`volume_${windowId}`);
    const indicatorContainer = document.getElementById(`indicator_${windowId}`);
    
    if (!candleContainer || !volumeContainer || !indicatorContainer) {
        console.error('找不到子图容器:', windowId);
        return;
    }
    
    console.log('创建三子图:', windowId);
    
    // 创建candle图
    const candleChart = LightweightCharts.createChart(candleContainer, {
        // width: '100%',
        // height: '100%',
        layout: {
            background: { color: '#1e222d' },
            textColor: '#ffffff',
        },
        grid: {
            vertLines: { color: '#2B2B43' },
            horzLines: { color: '#2B2B43' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Magnet,
        },
        rightPriceScale: {
            borderColor: '#2B2B43',
            visible: true,
            autoScale: true,
        },
        timeScale: {
            borderColor: '#2B2B43',
            timeVisible: true,
            secondsVisible: false,
            visible: true, // 显示时间轴以支持十字线
        },
        handleScroll: {
            mouseWheel: true,
            pressedMouseMove: true,
            horzTouchDrag: true,
            vertTouchDrag: true,
        },
        handleScale: {
            axisPressedMouseMove: true,
            mouseWheel: true,
            pinch: true,
        },
    });

    // 创建成交量图
    const volumeChart = LightweightCharts.createChart(volumeContainer, {
        // width: '100%',
        // height: '100%',
        layout: {
            background: { color: '#1e222d' },
            textColor: '#ffffff',
        },
        grid: {
            vertLines: { color: '#2B2B43' },
            horzLines: { color: '#2B2B43' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Magnet,
        },
        rightPriceScale: {
            borderColor: '#2B2B43',
            visible: true,
            autoScale: true,
        },
        timeScale: {
            borderColor: '#2B2B43',
            timeVisible: true,
            secondsVisible: false,
            visible: true, // 显示时间轴以支持十字线
        },
        handleScroll: {
            mouseWheel: true,
            pressedMouseMove: true,
            horzTouchDrag: true,
            vertTouchDrag: true,
        },
        handleScale: {
            axisPressedMouseMove: true,
            mouseWheel: true,
            pinch: true,
        },
    });

    // 创建技术指标图
    const indicatorChart = LightweightCharts.createChart(indicatorContainer, {
        // width: '100%',
        // height: '100%',
        layout: {
            background: { color: '#1e222d' },
            textColor: '#ffffff',
        },
        grid: {
            vertLines: { color: '#2B2B43' },
            horzLines: { color: '#2B2B43' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Magnet,
        },
        rightPriceScale: {
            borderColor: '#2B2B43',
            visible: true,
            autoScale: true,
        },
        timeScale: {
            borderColor: '#2B2B43',
            timeVisible: true,
            secondsVisible: false,
            visible: true, // 在底部显示时间轴
        },
        handleScroll: {
            mouseWheel: true,
            pressedMouseMove: true,
            horzTouchDrag: true,
            vertTouchDrag: true,
        },
        handleScale: {
            axisPressedMouseMove: true,
            mouseWheel: true,
            pinch: true,
        },
    });

    const symbolSelector = document.getElementById(`symbolSelector_${windowId}`);
    const onSymbolChange = (value) => {
        currentSymbol = value;
        console.log('标的切换:', currentSymbol);
        loadTargetData(window);
    };
    // 选择下拉或从键盘输入都会触发
    symbolSelector.addEventListener('change', (e) => onSymbolChange(e.target.value));
    symbolSelector.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            onSymbolChange(e.target.value);
        }
    });

    const candlestickSeries = candleChart.addSeries(LightweightCharts.CandlestickSeries, {
        upColor: '#ef5350',
        downColor: '#26a69a',
        borderVisible: false,
        wickUpColor: '#ef5350',
        wickDownColor: '#26a69a',
    });

    const ma5_series = candleChart.addSeries(LightweightCharts.LineSeries, {
        color: getIndicatorColor('ma5'),
        lineWidth: 1,
        title: 'MA5'
    });

    const ma10_series = candleChart.addSeries(LightweightCharts.LineSeries, {
        color: getIndicatorColor('ma10'),
        lineWidth: 1,
        title: 'MA10'
    });

    const ma20_series = candleChart.addSeries(LightweightCharts.LineSeries, {
        color: getIndicatorColor('ma20'),
        lineWidth: 1,
        title: 'MA20'
    });

    const ma60_series = candleChart.addSeries(LightweightCharts.LineSeries, {
        color: getIndicatorColor('ma60'),
        lineWidth: 1,
        title: 'MA60'
    });
    console.log('candle图系列创建成功:', candlestickSeries);

    const volumeSeries = volumeChart.addSeries(LightweightCharts.HistogramSeries, {
        priceFormat: {
            type: 'volume',
        },
    });
    console.log('成交量系列创建成功:', volumeSeries);

    const indicatorSeries = new Map();
    console.log('指标系列创建成功:', indicatorSeries);

    const type = windowElement.querySelector('.type-selector').value;
    const window = {
        windowId,
        type,
        candleChart,
        volumeChart,
        indicatorChart,
        candlestickSeries,
        ma5_series,
        ma10_series,
        ma20_series,
        ma60_series,
        volumeSeries,
        indicatorSeries: new Map(), // 技术指标系列
        timeframe,
        element: windowElement,
        indicators: new Map(),
    }
    loadTargetList(window);
    windows.set(windowId, window);

    updateWindowStatus(windowId, '三子图已创建');
}


function registerWindowsEvent(window) {
    const candleChart = window.candleChart;
    const volumeChart = window.volumeChart;
    const indicatorChart = window.indicatorChart;
    const candlestickSeries = window.candlestickSeries;
    const volumeSeries = window.volumeSeries;
    const indicatorSeries = window.indicatorSeries;

    // 时间轴变化监听 - 只同步时间轴范围
    candleChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if (isResizing || !timeRange || timeRange.from == null || timeRange.to == null) return;
        isResizing = true;
        if(volumeChart && volumeSeries) volumeChart.timeScale().setVisibleRange(timeRange);
        if(indicatorChart && indicatorSeries.size > 0) indicatorChart.timeScale().setVisibleRange(timeRange);
        requestAnimationFrame(() => {
            isResizing = false;
        });
    });

    volumeChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if (isResizing || !timeRange || timeRange.from == null || timeRange.to == null) return;
        isResizing = true;
        if(candleChart && candlestickSeries) candleChart.timeScale().setVisibleRange(timeRange);
        if(indicatorChart && indicatorSeries.size > 0) indicatorChart.timeScale().setVisibleRange(timeRange);
        requestAnimationFrame(() => {
            isResizing = false;
        });
    });

    indicatorChart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if (isResizing || !timeRange || timeRange.from == null || timeRange.to == null) return;
        isResizing = true;
        if(candleChart && candlestickSeries) candleChart.timeScale().setVisibleRange(timeRange);
        if(volumeChart && volumeSeries.size > 0) volumeChart.timeScale().setVisibleRange(timeRange);
        requestAnimationFrame(() => {
            isResizing = false;
        });
    });

    // 十字线移动监听 - 只同步十字线位置
    candleChart.subscribeCrosshairMove((param) => {
        if (param) {
            const dataPoint = param.seriesData.get(candlestickSeries);
            if(dataPoint && dataPoint.time) {
                volumeChart.setCrosshairPosition(0, dataPoint.time, volumeSeries);
                const it = indicatorSeries.values();
                const firstIndicator = it.next().value;
                if(firstIndicator) {
                    indicatorChart.setCrosshairPosition(0, dataPoint.time, firstIndicator);
                }
                return;
            }
            volumeChart.clearCrosshairPosition();
            indicatorChart.clearCrosshairPosition();
        }
    });

    volumeChart.subscribeCrosshairMove((param) => {
        if (param) {
            const dataPoint = param.seriesData.get(volumeSeries);
            if(dataPoint && dataPoint.time) {
                candleChart.setCrosshairPosition(0, dataPoint.time, candlestickSeries);
                const it = indicatorSeries.values();
                const firstIndicator = it.next().value;
                if(firstIndicator) {
                    indicatorChart.setCrosshairPosition(0, dataPoint.time, firstIndicator);
                }
                return;
            }
            candleChart.clearCrosshairPosition();
            indicatorChart.clearCrosshairPosition();
        }
    });

    indicatorChart.subscribeCrosshairMove((param) => {
        if (param &&param.time) {
            candleChart.setCrosshairPosition(0, param.time, candlestickSeries);
            volumeChart.setCrosshairPosition(0, param.time, volumeSeries);
            return;
        }
        candleChart.clearCrosshairPosition();
        volumeChart.clearCrosshairPosition();
    });

    requestAnimationFrame(() => {
        isResizing = false;
    });
}

// 切换时间框架
function changeTimeframe(windowId, newTimeframe) {
    const window = windows.get(windowId);
    if (!window) return;

    window.timeframe = newTimeframe;
    
    updateWindowStatus(windowId, '时间框架已更新');
}

function changeType(windowId, newType) {
    const window = windows.get(windowId);
    if (!window) {
        console.log('窗口不存在:', windowId);
        return;
    }
    window.type = newType;
    loadTargetList(window);
    updateWindowStatus(windowId, '类型已更新');
}

// 添加技术指标
async function updateIndicator(windowId, indicatorType) {
    if (!indicatorType || !currentProject || !currentStartDate || !currentEndDate) {
        console.log('请先选择标的和日期范围');
        showMessage('请先选择标的和日期范围', 'error');
        return;
    }
    const window = windows.get(windowId);
    if (!window) return;
    const type = window.type;
    const url = `${API_BASE_URL}/${type}/indicators?symbol=${currentProject}&start_date=${currentStartDate}&end_date=${currentEndDate}&indicator=${indicatorType}`;
    

    try {
        const response = await fetch(url);
        const data = await response.json();
        const indicatorChart = window.indicatorChart;
        window.indicatorSeries.forEach((series, key) => {
            indicatorChart.removeSeries(series);
        });
        window.indicatorSeries.clear();
        
        if (indicatorType === 'macd') {
            // MACD需要添加三个系列
            if (data.indicator.macd && data.indicator.signal && data.indicator.histogram) {
                // MACD线
                const macdSeries = window.indicatorChart.addSeries(LightweightCharts.LineSeries, {
                    color: getIndicatorColor('macd'),
                    lineWidth: 2,
                    title: getIndicatorTitle('macd'),
                });
                macdSeries.setData(data.indicator.macd);
                window.indicatorSeries.set('macd', macdSeries);
                
                // 信号线
                const signalSeries = window.indicatorChart.addSeries(LightweightCharts.LineSeries, {
                    color: getIndicatorColor('macd_signal'),
                    lineWidth: 2,
                    title: getIndicatorTitle('macd_signal'),
                });
                signalSeries.setData(data.indicator.signal);
                window.indicatorSeries.set('macd_signal', signalSeries);
                
                // 柱状图
                const histogramSeries = window.indicatorChart.addSeries(LightweightCharts.HistogramSeries, {
                    color: getIndicatorColor('macd_histogram'),
                    priceFormat: {
                        type: 'volume',
                    },
                });
                histogramSeries.setData(data.indicator.histogram);
                window.indicatorSeries.set('macd_histogram', histogramSeries);
                
                updateWindowStatus(windowId, 'MACD指标已添加');
            } else {
                console.log('MACD数据格式不正确');
            }
        } else if (data.indicator) {
            // 其他指标
            const indicatorSeries = indicatorChart.addSeries(LightweightCharts.LineSeries, {
                color: getIndicatorColor(indicatorType),
                lineWidth: 2,
                title: getIndicatorTitle(indicatorType),
            });
            
            indicatorSeries.setData(data.indicator);
            window.indicatorSeries.set(indicatorType, indicatorSeries);
            
            updateWindowStatus(windowId, `${getIndicatorTitle(indicatorType)}已添加`);
        }
        indicatorChart.timeScale().fitContent();
    } catch (error) {
        console.error('添加指标失败:', error);
        showMessage('添加指标失败', 'error');
    }
}

// 获取指标颜色
function getIndicatorColor(indicatorType) {
    const colors = {
        'ma5': '#ff9800',
        'ma10': '#ff5722',
        'ma20': '#ff9800',
        'ma60': '#ffc107',
        'rsi': '#9c27b0',
        'macd': '#2196f3',
        'macd_signal': '#ff5722',
        'macd_histogram': '#4caf50'
    };
    return colors[indicatorType] || '#ffffff';
}

// 获取指标标题
function getIndicatorTitle(indicatorType) {
    const titles = {
        'ma5': 'MA5',
        'ma10': 'MA10',
        'ma20': 'MA20',
        'ma60': 'MA60',
        'rsi': 'RSI(14)',
        'macd': 'MACD',
        'macd_signal': 'MACD Signal',
        'macd_histogram': 'MACD Histogram'
    };
    return titles[indicatorType] || indicatorType;
}

// 销毁窗口 - 适配三子图布局
function destroyWindow(windowId) {
    console.log('销毁窗口:', windowId);
    
    const window = windows.get(windowId);
    if (!window) {
        console.log('窗口不存在:', windowId);
        return;
    }

    try {
        // 销毁三个子图
        if (window.candleChart) {
            window.candleChart.remove();
        }
        if (window.volumeChart) {
            window.volumeChart.remove();
        }
        if (window.indicatorChart) {
            window.indicatorChart.remove();
        }
        
        // 销毁DOM元素
        if (window.element) {
            window.element.remove();
        }
        
        // 从窗口映射中删除
        windows.delete(windowId);
        console.log('窗口销毁完成:', windowId, '剩余窗口数:', windows.size);
    } catch (error) {
        console.error('销毁窗口失败:', error);
    }
}

// 更新窗口状态
function updateWindowStatus(windowId, status) {
    const window = windows.get(windowId);
    if (!window) return;

    const statusElement = window.element.querySelector('.status-bar span:first-child');
    statusElement.textContent = status;
}

// 切换主题
function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    
    const theme = isDarkTheme ? {
        background: { color: '#1e222d' },
        textColor: '#ffffff',
        grid: {
            vertLines: { color: '#2B2B43' },
            horzLines: { color: '#2B2B43' },
        },
        rightPriceScale: {
            borderColor: '#2B2B43',
        },
        timeScale: {
            borderColor: '#2B2B43',
        },
    } : {
        background: { color: '#ffffff' },
        textColor: '#333',
        grid: {
            vertLines: { color: '#f0f0f0' },
            horzLines: { color: '#f0f0f0' },
        },
        rightPriceScale: {
            borderColor: '#ddd',
        },
        timeScale: {
            borderColor: '#ddd',
        },
    };
    
    windows.forEach((window, windowId) => {
        try {
            if (window.candleChart) window.candleChart.applyOptions(theme);
            if (window.volumeChart) window.volumeChart.applyOptions(theme);
            if (window.indicatorChart) window.indicatorChart.applyOptions(theme);
        } catch (error) {
            console.error(`窗口 ${windowId} 主题切换失败:`, error);
        }
    });
}

// 窗口大小调整处理 - 适配三子图布局
window.addEventListener('resize', () => {
    windows.forEach((window, windowId) => {
        try {
            // 获取子图容器
            const candleContainer = document.getElementById(`candle_${windowId}`);
            const volumeContainer = document.getElementById(`volume_${windowId}`);
            const indicatorContainer = document.getElementById(`indicator_${windowId}`);
            
            // 调整三个子图的尺寸
            if (window.candleChart && candleContainer) {
                window.candleChart.applyOptions({
                    width: candleContainer.clientWidth,
                    height: candleContainer.clientHeight,
                });
            }
            
            if (window.volumeChart && volumeContainer) {
                window.volumeChart.applyOptions({
                    width: volumeContainer.clientWidth,
                    height: volumeContainer.clientHeight,
                });
            }
            
            if (window.indicatorChart && indicatorContainer) {
                window.indicatorChart.applyOptions({
                    width: indicatorContainer.clientWidth,
                    height: indicatorContainer.clientHeight,
                });
            }
            if (window.candleChart) {
                window.candleChart.timeScale().fitContent();
            }
            if (window.volumeChart) {
                window.volumeChart.timeScale().fitContent();
            }
            if (window.indicatorChart) {
                window.indicatorChart.timeScale().fitContent();
            }
            
            console.log(`窗口 ${windowId} 尺寸调整完成`);
        } catch (error) {
            console.error(`窗口 ${windowId} 尺寴调整失败:`, error);
        }
    });
});

// 显示图表布局说明
function showChartLayoutInfo() {
    const info = `
        <div style="background: #1e222d; color: #ffffff; padding: 20px; border-radius: 8px; max-width: 600px;">
            <h3>📊 图表布局说明</h3>
            <div style="margin: 15px 0;">
                <h4>🎯 三个子图区域：</h4>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin: 10px 0; padding: 10px; background: #2B2B43; border-radius: 4px;">
                        <strong>📈 candle图区域 (0%-60%)</strong><br>
                        <span style="color: #26a69a;">• 显示标的价格candle图</span><br>
                        <span style="color: #26a69a;">• 支持缩放和平移</span><br>
                        <span style="color: #26a69a;">• 右侧价格刻度</span>
                    </li>
                    <li style="margin: 10px 0; padding: 10px; background: #2B2B43; border-radius: 4px;">
                        <strong>📊 成交量区域 (60%-80%)</strong><br>
                        <span style="color: #26a69a;">• 显示成交量柱状图</span><br>
                        <span style="color: #26a69a;">• 独立的价格刻度</span><br>
                        <span style="color: #26a69a;">• 与candle图时间同步</span>
                    </li>
                    <li style="margin: 10px 0; padding: 10px; background: #2B2B43; border-radius: 4px;">
                        <strong>📉 技术指标区域 (80%-100%)</strong><br>
                        <span style="color: #26a69a;">• 显示技术指标线图</span><br>
                        <span style="color: #26a69a;">• 支持多种指标</span><br>
                        <span style="color: #26a69a;">• 独立的价格刻度</span>
                    </li>
                </ul>
            </div>
            <div style="margin: 15px 0;">
                <h4>🎨 颜色说明：</h4>
                <ul style="list-style: none; padding: 0;">
                    <li><span style="color: #26a69a;">🟢 绿色</span> - 上涨candle、成交量</li>
                    <li><span style="color: #ef5350;">🔴 红色</span> - 下跌candle</li>
                    <li><span style="color: #ff9800;">🟠 橙色</span> - MA均线</li>
                    <li><span style="color: #9c27b0;">🟣 紫色</span> - RSI指标</li>
                    <li><span style="color: #2196f3;">🔵 蓝色</span> - MACD指标</li>
                    <li><span style="color: #4caf50;">🟢 绿色</span> - 布林带</li>
                </ul>
            </div>
            <div style="margin: 15px 0;">
                <h4>🔧 操作说明：</h4>
                <ul style="list-style: none; padding: 0;">
                    <li>• 鼠标滚轮：缩放图表</li>
                    <li>• 拖拽：平移图表</li>
                    <li>• 十字线：同步所有子图</li>
                    <li>• 指标选择：在窗口标题栏选择</li>
                </ul>
            </div>
        </div>
    `;
    
    // 创建模态框显示信息
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    const content = document.createElement('div');
    content.innerHTML = info;
    content.style.cssText = `
        max-height: 80vh;
        overflow-y: auto;
        position: relative;
    `;
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        color: #ffffff;
        font-size: 24px;
        cursor: pointer;
        padding: 5px;
    `;
    closeBtn.onclick = () => modal.remove();
    
    content.appendChild(closeBtn);
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    // 点击背景关闭
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
}

// 页面加载完成后显示布局说明
// window.addEventListener('load', () => {
//     // 延迟显示，让用户先看到界面
//     setTimeout(() => {
//         showChartLayoutInfo();
//     }, 2000);
// });

// 初始化与全局导出（用于 HTML 内联事件调用）
document.addEventListener('DOMContentLoaded', () => {
    try {
        initLayout();
        setDefaultDates();
        createInitialWindows();

        const start = document.getElementById('startDate');
        const end = document.getElementById('endDate');
        if (start) start.addEventListener('blur', updateAllWindows);
        if (end) end.addEventListener('blur', updateAllWindows);
    } catch (error) {
        console.error('初始化失败:', error);
    }
});

// 将需要被 HTML 调用的函数挂载到 window
Object.assign(window, {
    createWindow,
    runProject,
    toggleTheme,
    onProjectSelect,
    executeRunProject,
    toggleProjectChartPanel,
    changeType,
    changeTimeframe,
    updateIndicator,
    destroyWindow,
});
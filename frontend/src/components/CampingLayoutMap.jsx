import { Box, Tooltip } from '@mui/material';
import { useState, useEffect, useRef } from 'react';

export default function CampingLayoutMap({ sites, selectedSites, onSiteClick }) {
  const canvasRef = useRef(null);
  const [hoveredSite, setHoveredSite] = useState(null);
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 });

  useEffect(() => {
    if (!sites || sites.length === 0) return;

    // 좌석 좌표의 최대/최소값 계산
    const xCoords = sites.map(s => s.x_coordinate);
    const yCoords = sites.map(s => s.y_coordinate);
    const maxX = Math.max(...xCoords) + 50;
    const maxY = Math.max(...yCoords) + 50;

    // 캔버스 크기 설정 (비율 유지하면서 화면에 맞게)
    const containerWidth = canvasRef.current?.parentElement?.offsetWidth || 800;
    const scale = containerWidth / maxX;
    setCanvasSize({
      width: containerWidth,
      height: maxY * scale
    });

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 배경 그리기 (잔디밭 느낌)
    ctx.fillStyle = '#e8f5e9';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 각 좌석 그리기
    sites.forEach(site => {
      const x = site.x_coordinate * scale;
      const y = site.y_coordinate * scale;
      const size = (site.width || 20) * scale;

      // 선택 여부 확인
      const selectedIndex = selectedSites.findIndex(s => s.product_code === site.product_code);
      const isSelected = selectedIndex !== -1;
      const isAvailable = site.select_yn === '1';

      // 좌석 상태에 따라 색상 결정
      let fillColor;
      let strokeColor;

      if (isSelected) {
        // 선택된 좌석: 파란색 + 우선순위 표시
        fillColor = '#1976d2';
        strokeColor = '#0d47a1';
      } else if (isAvailable) {
        // 예약 가능: 초록색
        fillColor = '#4caf50';
        strokeColor = '#2e7d32';
      } else {
        // 예약 불가: 회색
        fillColor = '#bdbdbd';
        strokeColor = '#757575';
      }

      // 호버 효과
      if (hoveredSite === site.product_code) {
        fillColor = '#ff9800';
        strokeColor = '#f57c00';
      }

      // 좌석 원 그리기
      ctx.beginPath();
      ctx.arc(x, y, size / 2, 0, 2 * Math.PI);
      ctx.fillStyle = fillColor;
      ctx.fill();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2;
      ctx.stroke();

      // 좌석 텍스트 (이름)
      ctx.fillStyle = '#fff';
      ctx.font = `bold ${Math.max(10, size / 3)}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const shortName = site.product_name.replace('금관-', '');
      ctx.fillText(shortName, x, y);

      // 선택된 경우 우선순위 배지
      if (isSelected) {
        const badgeSize = size / 2.5;
        ctx.beginPath();
        ctx.arc(x + size / 2.5, y - size / 2.5, badgeSize / 2, 0, 2 * Math.PI);
        ctx.fillStyle = '#ff5722';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = '#fff';
        ctx.font = `bold ${badgeSize / 1.5}px Arial`;
        ctx.fillText(selectedIndex + 1, x + size / 2.5, y - size / 2.5);
      }
    });

  }, [sites, selectedSites, hoveredSite, canvasSize.width]);

  const handleCanvasClick = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const scale = canvasSize.width / (Math.max(...sites.map(s => s.x_coordinate)) + 50);

    // 클릭한 위치에 있는 좌석 찾기
    const clickedSite = sites.find(site => {
      const siteX = site.x_coordinate * scale;
      const siteY = site.y_coordinate * scale;
      const size = (site.width || 20) * scale;
      const distance = Math.sqrt((x - siteX) ** 2 + (y - siteY) ** 2);
      return distance <= size / 2;
    });

    if (clickedSite) {
      onSiteClick(clickedSite);
    }
  };

  const handleCanvasHover = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const scale = canvasSize.width / (Math.max(...sites.map(s => s.x_coordinate)) + 50);

    // 호버 중인 좌석 찾기
    const hoveredSiteObj = sites.find(site => {
      const siteX = site.x_coordinate * scale;
      const siteY = site.y_coordinate * scale;
      const size = (site.width || 20) * scale;
      const distance = Math.sqrt((x - siteX) ** 2 + (y - siteY) ** 2);
      return distance <= size / 2;
    });

    setHoveredSite(hoveredSiteObj ? hoveredSiteObj.product_code : null);
    canvas.style.cursor = hoveredSiteObj ? 'pointer' : 'default';
  };

  return (
    <Box sx={{ position: 'relative', width: '100%' }}>
      {/* 범례 */}
      <Box sx={{ display: 'flex', gap: 3, mb: 2, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 20, height: 20, bgcolor: '#4caf50', borderRadius: '50%', border: '2px solid #2e7d32' }} />
          <span>예약 가능</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 20, height: 20, bgcolor: '#bdbdbd', borderRadius: '50%', border: '2px solid #757575' }} />
          <span>예약 불가</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 20, height: 20, bgcolor: '#1976d2', borderRadius: '50%', border: '2px solid #0d47a1' }} />
          <span>선택됨</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 20, height: 20, bgcolor: '#ff9800', borderRadius: '50%', border: '2px solid #f57c00' }} />
          <span>호버</span>
        </Box>
      </Box>

      {/* 캔버스 */}
      <Box
        sx={{
          border: '2px solid',
          borderColor: 'divider',
          borderRadius: 1,
          overflow: 'hidden',
          bgcolor: 'background.paper'
        }}
      >
        <canvas
          ref={canvasRef}
          width={canvasSize.width}
          height={canvasSize.height}
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasHover}
          onMouseLeave={() => setHoveredSite(null)}
          style={{ display: 'block', width: '100%', height: 'auto' }}
        />
      </Box>

      {/* 호버 툴팁 */}
      {hoveredSite && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 10,
            left: '50%',
            transform: 'translateX(-50%)',
            bgcolor: 'rgba(0,0,0,0.8)',
            color: 'white',
            px: 2,
            py: 1,
            borderRadius: 1,
            zIndex: 1000
          }}
        >
          {sites.find(s => s.product_code === hoveredSite)?.product_name} -{' '}
          {sites.find(s => s.product_code === hoveredSite)?.select_yn === '1'
            ? '예약 가능'
            : '예약 불가'}
        </Box>
      )}
    </Box>
  );
}

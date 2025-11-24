import { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import CampingLayoutMap from '../components/CampingLayoutMap';
import api from '../services/api';

export default function SiteSelection() {
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [sites, setSites] = useState([]);
  const [selectedSites, setSelectedSites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
  };

  const handleSearchSites = async () => {
    setLoading(true);
    setError(null);
    setSites([]);
    setSelectedSites([]);

    try {
      const formattedDate = selectedDate.format('YYYY-MM-DD');
      const response = await api.getXTicketSites(formattedDate);

      if (response.success) {
        setSites(response.sites);
      } else {
        setError('좌석 정보를 불러오는데 실패했습니다.');
      }
    } catch (err) {
      console.error('Failed to fetch sites:', err);
      setError(err.message || '좌석 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSiteClick = (site) => {
    // 이미 선택된 좌석인지 확인
    const isSelected = selectedSites.some(s => s.product_code === site.product_code);

    if (isSelected) {
      // 선택 해제
      setSelectedSites(selectedSites.filter(s => s.product_code !== site.product_code));
    } else {
      // 선택 추가 (최대 10개까지)
      if (selectedSites.length < 10) {
        setSelectedSites([...selectedSites, site]);
      } else {
        alert('최대 10개까지 선택할 수 있습니다.');
      }
    }
  };

  const handleRemoveSite = (productCode) => {
    setSelectedSites(selectedSites.filter(s => s.product_code !== productCode));
  };

  const handleMovePriority = (index, direction) => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === selectedSites.length - 1)
    ) {
      return;
    }

    const newSites = [...selectedSites];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [newSites[index], newSites[targetIndex]] = [newSites[targetIndex], newSites[index]];
    setSelectedSites(newSites);
  };

  const handleSaveSelection = () => {
    // 선택된 좌석을 LocalStorage에 저장
    const selectionData = {
      date: selectedDate.format('YYYY-MM-DD'),
      sites: selectedSites.map((site, index) => ({
        priority: index + 1,
        product_code: site.product_code,
        product_name: site.product_name,
        price: site.sale_product_fee || site.product_fee
      }))
    };

    localStorage.setItem('camping_site_selection', JSON.stringify(selectionData));
    alert('좌석 선택이 저장되었습니다!');
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          좌석 선택
        </Typography>

        {/* 날짜 선택 */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <DatePicker
                label="예약 날짜"
                value={selectedDate}
                onChange={handleDateChange}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Button
                variant="contained"
                onClick={handleSearchSites}
                disabled={loading}
                fullWidth
                size="large"
              >
                {loading ? <CircularProgress size={24} /> : '좌석 조회'}
              </Button>
            </Grid>
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Paper>

        {/* 캠핑장 배치도 */}
        {sites.length > 0 && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              캠핑장 배치도
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              좌석을 클릭하여 선택하세요. 선택한 순서가 예약 우선순위가 됩니다.
            </Typography>

            <CampingLayoutMap
              sites={sites}
              selectedSites={selectedSites}
              onSiteClick={handleSiteClick}
            />
          </Paper>
        )}

        {/* 선택된 좌석 목록 */}
        {selectedSites.length > 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              선택된 좌석 (우선순위 순)
            </Typography>

            <Box sx={{ mb: 2 }}>
              {selectedSites.map((site, index) => (
                <Box
                  key={site.product_code}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 2,
                    mb: 1,
                    bgcolor: 'background.default',
                    borderRadius: 1,
                    border: '1px solid',
                    borderColor: 'divider'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Chip label={`우선순위 ${index + 1}`} color="primary" />
                    <Typography variant="body1" fontWeight="bold">
                      {site.product_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {site.product_code}
                    </Typography>
                    <Typography variant="body2">
                      {(site.sale_product_fee || site.product_fee).toLocaleString()}원
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      onClick={() => handleMovePriority(index, 'up')}
                      disabled={index === 0}
                    >
                      ↑
                    </Button>
                    <Button
                      size="small"
                      onClick={() => handleMovePriority(index, 'down')}
                      disabled={index === selectedSites.length - 1}
                    >
                      ↓
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      onClick={() => handleRemoveSite(site.product_code)}
                    >
                      삭제
                    </Button>
                  </Box>
                </Box>
              ))}
            </Box>

            <Button
              variant="contained"
              color="primary"
              onClick={handleSaveSelection}
              fullWidth
              size="large"
            >
              선택 완료 및 저장
            </Button>
          </Paper>
        )}
      </Container>
    </LocalizationProvider>
  );
}

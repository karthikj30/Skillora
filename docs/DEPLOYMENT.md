# Skillora Deployment Guide

## Quick Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd Skillora
   python scripts/setup.py
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Load Sample Data (Optional)**
   ```bash
   python manage.py load_sample_data
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Production Deployment

### Environment Variables
Create a `.env` file based on `.env.example`:
- Set `DEBUG=False`
- Configure proper `SECRET_KEY`
- Set `ALLOWED_HOSTS`
- Configure database settings

### Static Files
```bash
python manage.py collectstatic
```

### Security Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS`
- [ ] Configure HTTPS
- [ ] Set up proper database
- [ ] Configure email backend
- [ ] Set up logging

## File Structure After Setup

The organized structure ensures:
- Easy maintenance
- Clear separation of concerns
- Scalable architecture
- Standard Django practices

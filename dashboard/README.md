# Multi-AI Orchestrator Dashboard

Production-ready MUI v7.3.7 dashboard built with Vite + React + TypeScript.

## 🚀 Quick Start

```bash
cd dashboard
npm install
npm run dev
```

Dashboard will be available at `http://localhost:5173`

## 📦 Features

- **MUI v7.3.7** - Latest Material-UI components
- **@mui/x-charts** - Professional data visualization
- **@mui/x-data-grid** - Advanced table components
- **Dark Theme** - Modern dark mode interface
- **Responsive Design** - Works on all screen sizes
- **TypeScript** - Full type safety
- **Vite** - Lightning fast builds

## 🏗️ Structure

```
dashboard/
├── src/
│   ├── App.tsx              # Main layout with AppBar
│   ├── main.tsx             # Entry point
│   └── views/
│       └── Dashboard/
│           ├── Dashboard.tsx    # Main dashboard grid
│           ├── Chart.tsx        # Line chart component
│           ├── Deposits.tsx     # Recent users card
│           ├── Orders.tsx       # Activity table
│           └── Title.tsx        # Reusable title component
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 🐳 Docker

```bash
docker-compose up dashboard
```

## 📝 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🎨 Customization

Edit `src/App.tsx` to customize:
- Theme colors
- Layout spacing
- Typography
- Component styles

import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Statewave',
  description: 'Memory OS for AI agents and applications',
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Getting Started', link: '/getting-started' },
      { text: 'API', link: '/api/v1-contract' },
      { text: 'Architecture', link: '/architecture/overview' },
    ],
    sidebar: [
      {
        text: 'Introduction',
        items: [
          { text: 'Why Statewave', link: '/why-statewave' },
          { text: 'Product', link: '/product' },
          { text: 'Getting Started', link: '/getting-started' },
          { text: 'Roadmap', link: '/roadmap' },
        ],
      },
      {
        text: 'API',
        items: [
          { text: 'V1 Contract', link: '/api/v1-contract' },
        ],
      },
      {
        text: 'Architecture',
        items: [
          { text: 'Overview', link: '/architecture/overview' },
          { text: 'Repo Map', link: '/architecture/repo-map' },
        ],
      },
      {
        text: 'ADRs',
        items: [
          { text: '001 - Postgres + pgvector', link: '/adrs/001-postgres-pgvector' },
          { text: '002 - Heuristic Compilation', link: '/adrs/002-heuristic-compilation' },
          { text: '003 - Production Hardening', link: '/adrs/003-v02-production-hardening' },
          { text: '004 - Advanced Features', link: '/adrs/004-v03-advanced-features' },
        ],
      },
      {
        text: 'Deployment',
        items: [
          { text: 'Guide', link: '/deployment/guide' },
          { text: 'Migrations', link: '/deployment/migrations' },
        ],
      },
      {
        text: 'Development',
        items: [
          { text: 'Conventions', link: '/dev/conventions' },
          { text: 'Backup & Restore', link: '/dev/backup-restore' },
          { text: 'Snapshots', link: '/dev/snapshots' },
        ],
      },
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/smaramwbc/statewave-docs' },
    ],
  },
})

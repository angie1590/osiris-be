// @ts-check

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Osiris ERP - Documentación Oficial',
  tagline: 'Docs-as-Code del backend de Osiris ERP',
  favicon: 'img/favicon.ico',

  url: 'http://localhost',
  baseUrl: '/',

  organizationName: 'open-latina',
  projectName: 'osiris-be',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'es',
    locales: ['es']
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          routeBasePath: '/',
          editUrl: undefined
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css')
        }
      })
    ]
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'light',
        disableSwitch: false,
        respectPrefersColorScheme: true
      },
      navbar: {
        title: 'Osiris ERP Docs',
        items: [
          { to: '/', label: 'Inicio', position: 'left' },
          { to: '/inventario/catalogo_atributos', label: 'Inventario EAV', position: 'left' }
        ]
      }
    })
};

module.exports = config;

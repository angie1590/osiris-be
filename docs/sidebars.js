/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'API',
      items: [
        {
          type: 'category',
          label: 'Common',
          items: [
            'api/common/onboarding',
            'api/common/seguridad-accesos',
            'api/common/directorio'
          ]
        },
        {
          type: 'category',
          label: 'Inventario',
          items: [
            'api/inventario/bloques-construccion',
            'api/inventario/casa-comercial-bodega',
            'inventario/producto-atributos-impuestos-bodegas',
            'api/inventario/producto-crud-base'
          ]
        }
      ]
    }
  ]
};

module.exports = sidebars;

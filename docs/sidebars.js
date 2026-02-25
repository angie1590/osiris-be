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
            'api/inventario/checklist-integracion-frontend',
            'api/inventario/bloques-construccion',
            'api/inventario/casa-comercial-bodega',
            'api/inventario/producto-atributos-impuestos-bodegas',
            'api/inventario/producto-crud-base'
          ]
        }
        ,
        {
          type: 'category',
          label: 'Transacciones',
          items: [
            'api/transacciones/compras'
          ]
        }
      ]
    }
  ]
};

module.exports = sidebars;

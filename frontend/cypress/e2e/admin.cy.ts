describe('Admin Pages', () => {
  beforeEach(() => {
    cy.login('demo@esgadvisor.ai', 'demo1234')
  })

  it('Fonds Verts list loads with data', () => {
    cy.visit('/admin/fonds')

    cy.contains('Fonds Verts').should('be.visible')
    cy.contains('Nouveau Fonds').should('be.visible')
    cy.get('table, [class*="table"]').should('be.visible')
    cy.contains('BOAD').should('be.visible')
  })

  it('Référentiels list loads with items', () => {
    cy.visit('/admin/referentiels')

    cy.contains('Référentiels ESG').should('be.visible')
    cy.contains('Nouveau').should('be.visible')
    cy.contains('BCEAO').should('be.visible')
  })

  it('Skills list loads with skill cards', () => {
    cy.visit('/admin/skills')

    cy.contains('Skills').should('be.visible')
    cy.get('[class*="card"], [class*="border"]').should('have.length.gte', 1)
  })
})

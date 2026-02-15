import { describe, it, expect } from 'vitest'

// Test du pattern matching utilise dans le detector
function matchUrl(url: string, pattern: string): boolean {
  const regex = new RegExp(
    '^' + pattern
      .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '.*')
    + '$'
  )
  return regex.test(url)
}

describe('URL Pattern Matching', () => {
  it('matche une URL exacte', () => {
    expect(matchUrl(
      'https://www.boad.org/appels-a-projets',
      'https://www.boad.org/appels-a-projets'
    )).toBe(true)
  })

  it('matche un pattern avec wildcard a la fin', () => {
    expect(matchUrl(
      'https://www.boad.org/appels-a-projets/fonds-vert',
      'https://www.boad.org/appels-a-projets/*'
    )).toBe(true)
  })

  it('matche un pattern avec wildcard au milieu', () => {
    expect(matchUrl(
      'https://www.boad.org/appels-a-projets/fonds-vert/candidature',
      'https://www.boad.org/*appels*/candidature'
    )).toBe(true)
  })

  it('ne matche pas une URL differente', () => {
    expect(matchUrl(
      'https://www.google.com',
      'https://www.boad.org/*'
    )).toBe(false)
  })

  it('matche avec wildcard unique', () => {
    expect(matchUrl(
      'https://example.com/anything',
      'https://example.com/*'
    )).toBe(true)
  })

  it('ne matche pas un sous-domaine different', () => {
    expect(matchUrl(
      'https://api.boad.org/test',
      'https://www.boad.org/*'
    )).toBe(false)
  })

  it('matche les caracteres speciaux dans le domaine', () => {
    expect(matchUrl(
      'https://www.boad.org/test',
      'https://www.boad.org/*'
    )).toBe(true)
  })

  it('matche un pattern complexe avec plusieurs wildcards', () => {
    expect(matchUrl(
      'https://www.greenclimate.fund/projects/apply/form',
      'https://www.greenclimate.fund/*/apply/*'
    )).toBe(true)
  })

  it('ne matche pas quand le chemin est trop court', () => {
    expect(matchUrl(
      'https://www.boad.org',
      'https://www.boad.org/appels/*'
    )).toBe(false)
  })
})

import { it, expect } from 'vitest'
import { qidiBoxSlots } from '../qidi-box'

it('reads Q2 flat native slot identity, color and RFID scan state', () => {
 const printer = { save_variables: { variables: { box_count: 1 } }, multi_color_controller: { box: {
  box0_filament_info_1_filament_id: 'QFX11',
  box0_filament_info_1_filament_str: 'Anycubic PETG',
  box0_filament_info_1_filament_type: 'PETG',
  box0_filament_info_1_vendor_str: 'Anycubic',
  box0_filament_info_1_color_rgb_str: ['003594'],
  box0_filament_info_1_read_rfid_state: 1
 } } }
 const slot = qidiBoxSlots(printer, null).find(s => s.index === 1)!
 expect(slot.filamentId).toBe('QFX11')
 expect(slot.name).toBe('Anycubic PETG')
 expect(slot.reading).toBe(true)
})

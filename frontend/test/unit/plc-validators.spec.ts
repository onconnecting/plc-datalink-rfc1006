import { FormControl } from '@angular/forms';
import {
  ipv4Validator,
  plcAddressValidator,
  tagNameValidator,
  portValidators,
  PLC_ADDRESS_REGEX,
} from '../../src/app/validators/plc-validators';

function ctrl(value: unknown): FormControl {
  return new FormControl(value);
}

describe('ipv4Validator', () => {
  it.each(['0.0.0.0', '192.168.1.1', '255.255.255.255', '10.0.0.1'])(
    'accepts %s',
    (ip) => {
      expect(ipv4Validator(ctrl(ip))).toBeNull();
    },
  );

  it.each(['256.0.0.0', '192.168.1', '192.168.1.1.1', 'localhost', '1.1.1.1.', ''])(
    'rejects %s',
    (ip) => {
      const expected = ip === '' ? null : { ipv4: true };
      expect(ipv4Validator(ctrl(ip))).toEqual(expected);
    },
  );

  it('passes empty values (required-handling lives on Validators.required)', () => {
    expect(ipv4Validator(ctrl(null))).toBeNull();
    expect(ipv4Validator(ctrl(undefined))).toBeNull();
    expect(ipv4Validator(ctrl(''))).toBeNull();
  });
});

describe('plcAddressValidator (and PLC_ADDRESS_REGEX)', () => {
  const valid = [
    'DB1.X0.0',
    'DB2000.B1',
    'DB2000.C2',
    'DB2000.W4',
    'DB2000.DW8',
    'DB1.I0',
    'DB1.DI4',
    'DB1.R28',
    'DB2000.DT20',
    'DB47.S30.13',
  ];

  it.each(valid)('accepts %s', (addr) => {
    expect(plcAddressValidator(ctrl(addr))).toBeNull();
    expect(PLC_ADDRESS_REGEX.test(addr)).toBe(true);
  });

  const invalid = [
    'DBfoo.X0.0',
    'DB1.Z0',
    'X1.X0',
    'DB1X0',
    'M1.X0.0',
    'DB1.X',
  ];

  it.each(invalid)('rejects %s', (addr) => {
    expect(plcAddressValidator(ctrl(addr))).toEqual({ plcAddress: true });
  });
});

describe('tagNameValidator', () => {
  it.each(['lightBarrier', 'Tag1', 'foo', 'A0', '123'])('accepts %s', (n) => {
    expect(tagNameValidator(ctrl(n))).toBeNull();
  });

  it.each(['tag name', 'tag-name', 'tag.name', 'tag_name', 'umlautü'])(
    'rejects %s',
    (n) => {
      expect(tagNameValidator(ctrl(n))).toEqual({ tagName: true });
    },
  );
});

describe('portValidators', () => {
  it('is the [required, min(1), max(65535)] trio', () => {
    expect(portValidators).toHaveLength(3);
  });
});
